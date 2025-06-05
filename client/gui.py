import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import streamlit as st

from client import TCPClient


class OperationSelector:
    
    def select_operation(self):
        option = st.selectbox(
            "変換オプションを選択",
            ["圧縮", "解像度変更", "アスペクト比変更", "音声変換", "GIF作成"]
        )

        if option == "圧縮":
            code = 1
            details = self.compression_params()
            
        elif option == "解像度変更":
            code = 2
            details = self.resolution_params()
            
        elif option == "アスペクト比変更":
            code = 3
            details = self.aspect_ratio_params()
            
        elif option == "音声変換":
            code = 4
            details = {}
            
        else:  # GIF作成
            code = 5
            details = self.gif_params()
            
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
                "継続時間 (秒)", ""
            )
        }


class MediaRenderer:
    
    # 「変換前 → 変換後」の比較画面を2カラムで表示
    def show_before_after(self, original_path, result_path, conversion_type_code):
        self.show_compare_header()
        col1, col2 = st.columns(2)
        with col1:
            self.display_media(original_path, "video")
        with col2:
            self.show_converted(result_path, conversion_type_code)

    # 比較用のラベル（変換前 → 変換後）を表示
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

    def display_media(self, media_file_path, media_type):
        if media_type == "video":
            st.video(media_file_path)
        else:
            st.audio(media_file_path)

    def show_converted(self, result_path, conversion_type_code):
        # 圧縮・解像度変更・アスペクト比変更
        if conversion_type_code in (1, 2, 3):
            self.display_media(result_path, "video")
            
        # 音声変換
        elif conversion_type_code == 4:
            self.display_media(result_path, "audio")
            
        # GIF作成
        else:
            st.image(result_path)

        self.download_converted(result_path)

    # 変換後メディアをダウンロードできるボタンを表示
    def download_converted(self, result_path):
        st.download_button(
            label="変換後の動画をダウンロード",
            data=Path(result_path).read_bytes(),
            file_name=Path(result_path).name,
            mime="video/mp4"
        )
        

class VideoConverter:
    
    def __init__(self, client):
        self.client = client

    def convert(self, uploaded_file_path, conversion_type_code, conversion_params, show_progress):
        # 進捗を0%で初期化（開始時）
        show_progress(0)

        # スレッドプールを使って非同期に変換処理を実行
        with ThreadPoolExecutor() as executor:
            # アップロードおよび変換処理を別スレッドで開始
            future = executor.submit(
                self.client.upload_and_process,
                uploaded_file_path,
                conversion_type_code,
                conversion_params
            )

            percent = 0
            # 処理が完了するまで定期的に進捗を報告（最大95%まで）
            while not future.done():
                time.sleep(0.2)  # 200ミリ秒ごとに進捗確認
                percent = min(percent + 2, 95)  # 過剰に進まないよう上限を95%に制限
                show_progress(percent)

            # 処理完了後、変換結果のファイルパスを取得
            converted_file_path = future.result()

        # 進捗を100%に更新（完了時）
        show_progress(100)

        return converted_file_path


class StreamlitApp:

    def __init__(self, converter, selector, renderer):
        self.converter = converter
        self.selector = selector
        self.renderer = renderer
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
        # Streamlit ページの基本設定
        st.set_page_config(
            page_title="Video Processor",
            page_icon="🎥",
            layout="centered"
        )

        style_path = Path(__file__).parent / "style.css"

        style_html = (
            "<style>"
            f"{style_path.read_text()}"
            "</style>"
            '<div class="app-scale">'
        )

        st.markdown(style_html, unsafe_allow_html=True)

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

        if st.button("処理開始"):
            # プログレスバーを初期化（0%からスタート）
            self.progress_bar = st.progress(0)
            # ステータス表示用の空要素を作成（後で動的に更新）
            self.status_text = st.empty()

            try:
                # 実際の変換処理を非同期で実行し、変換後ファイルのパスを取得
                converted_file_path = self.converter.convert(
                    uploaded_file_path,
                    conversion_type_code,
                    conversion_params,
                    self.show_progress
                )
                
            except Exception as error:
                # 変換中にエラーが発生した場合はエラーメッセージを表示
                st.error(f"処理失敗: {error}")
                return

            st.success("✅ 処理完了！")
            # 元のメディアと変換後メディアを並べて表示
            self.renderer.show_before_after(uploaded_file_path, converted_file_path, conversion_type_code)


    def show_progress(self, progress_percent):
        # プログレスバーとステータス表示を進捗に応じて更新
        self.progress_bar.progress(progress_percent)
        self.status_text.text(f"変換進行中... {progress_percent}%")



if __name__ == "__main__":
    
    # サーバーの IPアドレス と ポート番号、および受信ディレクトリを設定
    server_address = "0.0.0.0"
    server_port = 9001
    receive_dir = "receive"

    # TCP クライアントを作成
    tcp_client = TCPClient(server_address, server_port, receive_dir)

    #各コンポーネントを初期化（変換ロジック・操作選択・メディア表示）
    converter = VideoConverter(tcp_client)
    selector = OperationSelector()
    renderer = MediaRenderer()

    # Streamlit アプリを起動
    streamlit_app = StreamlitApp(converter, selector, renderer)
    streamlit_app.start_streamlit_app()
