import streamlit as st
from client import TCPClient, FileHandler
import os
import tempfile
import base64
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

class ConversionService:
    """
    ファイルアップロードから変換処理、進捗通知までを担当するサービスクラス
    """
    def __init__(self,
                 server_address: str = "0.0.0.0",
                 server_port: int = 9001,
                 handler: FileHandler = None):
        self.handler = handler or FileHandler()
        self.client = TCPClient(
            server_address=server_address,
            server_port=server_port,
            handler=self.handler
        )

    def convert(self,
                input_path: str,
                operation: int,
                details: dict,
                progress_callback=None) -> str:
        """
        ファイルをサーバへアップロードし、変換を実行。進捗をコールバックで通知し、
        変換後のファイルパスを返す。
        """
        # 開始時 0%
        if progress_callback:
            progress_callback(0)

        # 非同期処理を使って upload_and_process を実行
        def _task():
            return self.client.upload_and_process(
                input_path,
                operation=operation,
                operation_details=details
            )

        with ThreadPoolExecutor() as executor:
            future = executor.submit(_task)
            pct = 0
            # 完了前は 2% ずつ擬似進捗
            while not future.done():
                time.sleep(0.2)
                pct = min(pct + 2, 95)
                if progress_callback:
                    progress_callback(pct)
            out_path = future.result()

        # 完了時 100%
        if progress_callback:
            progress_callback(100)

        return out_path

class MediaConverterApp:
    """
    Streamlit UI を管理し、ユーザーインタラクションを制御するアプリ本体クラス
    """
    def __init__(self):
        self.converter = ConversionService()
        self.prog_bar = None
        self.status = None

    def setup_page(self):
        """ページの共通設定と CSS 読み込み＋ラッパー <div> 開始タグ"""
        st.set_page_config(
            page_title="メディア変換ツール",
            page_icon="🎞️",
            layout="centered"
        )
        css = Path(__file__).parent / "style.css"
        st.markdown(
            f"<style>{css.read_text()}</style>\n<div class=\"app-scale\">",
            unsafe_allow_html=True
        )

    def get_uploaded_file(self) -> str:
        """
        ファイルアップロード UI を表示し、一時ディレクトリに保存してパスを返す。
        アップロードがなければ None。
        """
        uploaded = st.file_uploader("", type=["mp4", "avi", "mpeg4"])
        if uploaded is None:
            return None

        tmp_dir = tempfile.gettempdir()
        file_path = os.path.join(tmp_dir, uploaded.name)
        Path(file_path).write_bytes(uploaded.getbuffer())
        return file_path

    def select_operation(self):
        """
        変換オプションとパラメータ入力をまとめて行い、コード・詳細を返す。
        """
        op = st.selectbox(
            "変換オプションを選択",
            ["圧縮", "解像度変更", "アスペクト比変更", "音声変換", "GIF作成"]
        )

        details = {}
        if op == "圧縮":
            details["bitrate"] = st.selectbox("ビットレート", ["500k", "1M", "2M"])
            code = 1
        elif op == "解像度変更":
            details["resolution"] = st.selectbox("解像度", ["1920:1080", "1280:720", "720:480"])
            code = 2
        elif op == "アスペクト比変更":
            details["aspect_ratio"] = st.selectbox("アスペクト比", ["16/9", "4/3", "1/1"])
            code = 3
        elif op == "音声変換":
            code = 4
        else:
            details["start_time"] = st.text_input("開始時間 (秒)", "10")
            details["duration"] = st.text_input("継続時間 (秒)", "5")
            code = 5

        return code, details, op

    def _update_progress(self, percent: int):
        """
        プログレスバーとステータステキストを更新するコールバック
        """
        if self.prog_bar and self.status:
            self.prog_bar.progress(percent)
            self.status.text(f"変換進行中... {percent}%")

    def autoplay_media(self, path: str, media_type: str):
        """
        動画または音声ファイルを base64 で埋め込み、autoplay させる。
        """
        mime = {"video": "video/mp4", "audio": "audio/mpeg"}
        ext = Path(path).suffix.lower()
        if ext == ".avi":
            mime["video"] = "video/avi"

        data = Path(path).read_bytes()
        b64 = base64.b64encode(data).decode()

        if media_type == "video":
            html = f"""
            <video width="100%" controls autoplay loop playsinline>
              <source src="data:{mime['video']};base64,{b64}" type="{mime['video']}">
            </video>
            """
        else:
            html = f"""
            <audio controls autoplay style="width:100%;">
              <source src="data:{mime['audio']};base64,{b64}" type="{mime['audio']}">
            </audio>
            """
        st.markdown(html, unsafe_allow_html=True)

    def show_before_after(self, before_path: str, after_path: str, code: int):
        """
        変換前後を左右に並べて表示し、必要に応じてダウンロードボタンを設置。
        """
        st.markdown(
            """
            <div class="before-after">
              <div class="label">変換前</div>
              <div class="arrow">→</div>
              <div class="label">変換後</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        col1, col2 = st.columns(2)

        with col1:
            self.autoplay_media(before_path, "video")

        with col2:
            if code == 4:
                self.autoplay_media(after_path, "audio")
            elif code == 5:
                st.image(after_path)
            else:
                self.autoplay_media(after_path, "video")
                data = Path(after_path).read_bytes()
                st.download_button(
                    label="変換後の動画をダウンロード",
                    data=data,
                    file_name=Path(after_path).name,
                    mime="video/mp4"
                )

    def run(self):
        """アプリのエントリーポイント"""
        self.setup_page()

        file_path = self.get_uploaded_file()
        if not file_path:
            return

        code, details, _ = self.select_operation()

        if st.button("処理開始"):
            # プログレスバーとステータス用の UI を初期化
            self.prog_bar = st.progress(0)
            self.status = st.empty()
            try:
                out_path = self.converter.convert(
                    input_path=file_path,
                    operation=code,
                    details=details,
                    progress_callback=self._update_progress
                )
                st.success("✅ 処理完了！")
                self.show_before_after(file_path, out_path, code)
            except Exception as e:
                st.error(f"処理失敗: {e}")

        # ラッパー <div> の閉じタグ
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    MediaConverterApp().run()
