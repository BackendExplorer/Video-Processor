import os
import time
import base64
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import streamlit as st

from client import TCPClient


# ===== 変換オプション選択ロジック =====
class OperationSelector:
    
    def select_operation(self):
        option = st.selectbox(
            "変換オプションを選択",
            ["圧縮", "解像度変更", "アスペクト比変更", "音声変換", "GIF作成"]
        )

        if option == "圧縮":
            details = self.compression_params()
            code = 1
        elif option == "解像度変更":
            details = self.resolution_params()
            code = 2
        elif option == "アスペクト比変更":
            details = self.aspect_ratio_params()
            code = 3
        elif option == "音声変換":
            details = {}
            code = 4
        else:  # GIF作成
            details = self.gif_params()
            code = 5

        return code, details, option

    # ---------- 各オプションの入力 UI ----------    
    def compression_params(self):
        bitrate_options = ["500k", "1M", "2M"]
        return {
            "bitrate": st.selectbox("ビットレート", bitrate_options)
        }

    def resolution_params(self):
        resolution_options = ["1920:1080", "1280:720", "720:480"]
        return {
            "resolution": st.selectbox("解像度", resolution_options)
        }

    def aspect_ratio_params(self):
        aspect_ratio_options = ["16/9", "4/3", "1/1"]
        return {
            "aspect_ratio": st.selectbox("アスペクト比", aspect_ratio_options)
        }

    def gif_params(self):
        return {
            "start_time": st.text_input(
                "開始時間 (秒)", ""
            ),
            "duration": st.text_input(
                "続續時間 (秒)", ""
            )
        }


# ===== メディア表示ロジック =====
class MediaRenderer:
    """
    変換前後メディアの表示／ダウンロード UI を担当
    """

    # =========  メディア自動再生  =========
    def autoplay_media(self, media_file_path, media_type):
        mime_types = {"video": "video/mp4", "audio": "audio/mpeg"}
        ext = Path(media_file_path).suffix.lower()
        if ext == ".avi":
            mime_types["video"] = "video/avi"

        media_data = Path(media_file_path).read_bytes()
        media_b64 = base64.b64encode(media_data).decode()

        if media_type == "video":
            html = f"""
            <video width="100%" controls autoplay loop playsinline>
              <source src="data:{mime_types['video']};base64,{media_b64}" type="{mime_types['video']}">
            </video>
            """
        else:
            html = f"""
            <audio controls autoplay style="width:100%;">
              <source src="data:{mime_types['audio']};base64,{media_b64}" type="{mime_types['audio']}">
            </audio>
            """

        st.markdown(html, unsafe_allow_html=True)

    # =========  比較表示  =========
    def show_before_after(self, original_path, result_path, conversion_type_code):
        self.show_compare_header()
        col1, col2 = st.columns(2)
        with col1:
            # 変換前メディアを直接表示
            self.autoplay_media(original_path, "video")
        with col2:
            self.show_converted(result_path, conversion_type_code)

    # ---------- 比較画面ヘルパ ----------
    def show_compare_header(self):
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

    def show_converted(self, result_path, conversion_type_code):
        if conversion_type_code == 4:
            self.autoplay_media(result_path, "audio")
        elif conversion_type_code == 5:
            st.image(result_path)
        else:
            self.autoplay_media(result_path, "video")
            self.download_converted(result_path)

    def download_converted(self, result_path):
        converted_data = Path(result_path).read_bytes()
        st.download_button(
            label="変換後の動画をダウンロード",
            data=converted_data,
            file_name=Path(result_path).name,
            mime="video/mp4"
        )


# ===== サーバーとの通信・変換処理 =====
class VideoConverter:
    def __init__(self, server_address="0.0.0.0", server_port=9001, receive_dir="receive"):
        self.client = TCPClient(
            server_address=server_address,
            server_port=server_port,
            dpath=receive_dir
        )

    # 指定ファイルをサーバへアップロードし、変換処理を実行
    # 処理完了後は変換済みファイルの保存パスを返す
    def convert(self, uploaded_file_path, conversion_type_code, conversion_params, progress_callback=None):
        if progress_callback:
            progress_callback(0)

        def conversion_task():
            return self.client.upload_and_process(
                uploaded_file_path,
                operation=conversion_type_code,
                operation_details=conversion_params
            )

        with ThreadPoolExecutor() as executor:
            future = executor.submit(conversion_task)
            progress_percent = 0
            while not future.done():
                time.sleep(0.2)
                progress_percent = min(progress_percent + 2, 95)
                if progress_callback:
                    progress_callback(progress_percent)

            converted_file_path = future.result()

        if progress_callback:
            progress_callback(100)

        return converted_file_path


class StreamlitApp:

    def __init__(self):
        self.converter = VideoConverter()
        self.selector = OperationSelector()
        self.renderer = MediaRenderer()
        self.progress_bar = None
        self.status_text = None

    def start_streamlit_app(self):
        # ページの初期設定（タイトルやスタイルの読み込み）
        self.setup_page()
        # アップロードした動画ファイルを、一時的に保存したパスを取得
        uploaded_file_path = self.get_uploaded_file()
        # 動画の変換処理を実行
        self.handle_conversion(uploaded_file_path)
        # ページ下部のスケール用 DIV を閉じる
        st.markdown("</div>", unsafe_allow_html=True)

    def setup_page(self):
        st.set_page_config(
            page_title="Video Processor",
            page_icon="🎥",
            layout="centered"
        )

        css = Path(__file__).parent / "style.css"
        st.markdown(
            f"<style>{css.read_text()}</style>\n<div class=\"app-scale\">",
            unsafe_allow_html=True
        )

    def get_uploaded_file(self):
        uploaded_file = st.file_uploader("", type=["mp4", "avi", "mpeg4"])
        tmp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(tmp_dir, uploaded_file.name)
        Path(temp_file_path).write_bytes(uploaded_file.getbuffer())
        return temp_file_path

    def handle_conversion(self, uploaded_file_path):
        conversion_type_code, conversion_params, _ = self.selector.select_operation()

        if st.button("処理開始"):
            self.init_progress_ui()
            try:
                converted_file_path = self.execute_conversion(
                    uploaded_file_path,
                    conversion_type_code,
                    conversion_params
                )
                st.success("✅ 処理完了！")
                self.renderer.show_before_after(uploaded_file_path, converted_file_path, conversion_type_code)
            except Exception as error:
                st.error(f"処理失敗: {error}")

    def init_progress_ui(self):
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()

    def execute_conversion(self, path, code, params):
        return self.converter.convert(
            path, code, params, self.update_progress
        )

    def update_progress(self, progress_percent):
        if self.progress_bar and self.status_text:
            self.progress_bar.progress(progress_percent)
            self.status_text.text(f"変換進行中... {progress_percent}%")



if __name__ == "__main__":

    streamlit_app = StreamlitApp()
    streamlit_app.start_streamlit_app()
