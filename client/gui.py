import os
import time
import base64
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import streamlit as st

from client import TCPClient


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

        return code, details

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


class MediaRenderer:
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


class VideoConverter:
    def __init__(self, server_address="0.0.0.0", server_port=9001, receive_dir="receive"):
        # TCPクライアントを初期化（指定されたサーバーアドレスとポートで接続）
        self.client = TCPClient(server_address, server_port, dpath=receive_dir)

    # 指定されたファイルをサーバーにアップロードし、変換処理を実行する
    # 処理完了後、変換後ファイルの保存パスを返す
    def convert(self, uploaded_file_path, conversion_type_code, conversion_params, progress_callback=None):
        # プログレスバーの初期値（0%）を設定
        if progress_callback:
            progress_callback(0)

        # サーバーへのアップロードと変換処理を別スレッドで実行する関数
        def conversion_task():
            return self.client.upload_and_process(
                uploaded_file_path,
                operation=conversion_type_code,
                operation_details=conversion_params
            )

        # スレッドプールを使って非同期で変換処理を実行
        with ThreadPoolExecutor() as executor:
            future = executor.submit(conversion_task)
            progress_percent = 0
            # 処理が完了するまで進捗を定期的に更新（最大95%まで）
            while not future.done():
                time.sleep(0.2)
                progress_percent = min(progress_percent + 2, 95)
                if progress_callback:
                    progress_callback(progress_percent)

            # 処理結果（変換後ファイルのパス）を取得
            converted_file_path = future.result()

        # 処理完了後に進捗を100%に更新
        if progress_callback:
            progress_callback(100)

        # 変換後のファイルパスを返す
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
        if not uploaded_file_path:
            return  # ファイル未選択なら終了
        # 動画の変換処理を実行
        self.handle_conversion(uploaded_file_path)
        # ページ下部のスケール用 DIV を閉じる
        st.markdown("</div>", unsafe_allow_html=True)

    # ページの初期設定（タイトルやスタイルの読み込み）
    def setup_page(self):
        # Streamlit ページの基本設定（タイトル、アイコン、レイアウト）を指定
        st.set_page_config(
            page_title="Video Processor",
            page_icon="🎥",
            layout="centered"
        )

        # スタイルシート（style.css）を読み込み、ページ全体の見た目を調整
        css = Path(__file__).parent / "style.css"
        st.markdown(
            f"<style>{css.read_text()}</style>\n<div class=\"app-scale\">",
            unsafe_allow_html=True
        )

    # アップロードしたファイルを一時的なパスに保存する
    def get_uploaded_file(self):
        # ファイルアップロード用のウィジェットを表示（対応形式は mp4, avi, mpeg4）
        uploaded_file = st.file_uploader("", type=["mp4", "avi", "mpeg4"])
        if uploaded_file is None:
            return None  # ファイルが未選択なら None を返す

        # 一時ディレクトリのパスを取得する
        tmp_dir = tempfile.gettempdir()

        # アップロードされたファイルを一時ファイルとして保存するパスを作成
        temp_file_path = os.path.join(tmp_dir, uploaded_file.name)

        # アップロードされたファイルの内容を一時ファイルに書き込む
        Path(temp_file_path).write_bytes(uploaded_file.getbuffer())

        # 一時ファイルのパスを返す
        return temp_file_path

    # 動画の変換処理を実行
    def handle_conversion(self, uploaded_file_path):
        # ユーザーが選択した変換オプションとそのパラメータを取得
        conversion_type_code, conversion_params = self.selector.select_operation()

        # 「処理開始」ボタンがクリックされたら変換処理を実行
        if st.button("処理開始"):
            # プログレスバーとステータステキストの初期化
            self.init_progress_ui()
            try:
                # 実際の変換処理を非同期で実行し、変換後ファイルのパスを取得
                converted_file_path = self.execute_conversion(
                    uploaded_file_path,
                    conversion_type_code,
                    conversion_params
                )
                # 処理が正常に完了したことをユーザーに通知
                st.success("✅ 処理完了！")
                # 元のメディアと変換後メディアを並べて表示
                self.renderer.show_before_after(uploaded_file_path, converted_file_path, conversion_type_code)
            except Exception as error:
                # 変換中にエラーが発生した場合はエラーメッセージを表示
                st.error(f"処理失敗: {error}")

    def init_progress_ui(self):
        # プログレスバーを初期化（0%からスタート）
        self.progress_bar = st.progress(0)
        # ステータス表示用の空要素を作成（後で動的に更新）
        self.status_text = st.empty()

    def execute_conversion(self, path, code, params):
        # 変換処理を実行し、進捗更新用のコールバックを渡す
        return self.converter.convert(
            path, code, params, self.update_progress
        )

    def update_progress(self, progress_percent):
        # プログレスバーとステータス表示を進捗に応じて更新
        if self.progress_bar and self.status_text:
            self.progress_bar.progress(progress_percent)
            self.status_text.text(f"変換進行中... {progress_percent}%")


if __name__ == "__main__":

    streamlit_app = StreamlitApp()
    streamlit_app.start_streamlit_app()
