import os
import time
import base64
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import streamlit as st

from client import TCPClient


class ConversionService:
    
    def __init__(self, server_address = "0.0.0.0",
                 server_port = 9001,
                 receive_dir = "receive"):
        self.client = TCPClient(
            server_address=server_address,
            server_port=server_port,
            dpath=receive_dir
        )

    # 指定ファイルをサーバへアップロードし、変換処理を実行
    # 処理完了後は変換済みファイルの保存パスを返す
    def convert(self,
                input_path,
                operation_code,
                operation_params,
                progress_callback=None):
        
        # 処理開始時に進捗を 0% にリセット
        if progress_callback:
            progress_callback(0)

        # サーバとの通信・変換処理を別スレッドで実行するタスク
        def task():
            return self.client.upload_and_process(
                input_path,
                operation=operation_code,
                operation_details=operation_params
            )

        # スレッドプールを用いて非同期で変換処理を実行
        with ThreadPoolExecutor() as executor:
            future = executor.submit(task)
            progress_percent = 0

            # 変換処理が完了するまで疑似的な進捗を更新（最大 95%）
            while not future.done():
                time.sleep(0.2)
                progress_percent = min(progress_percent + 2, 95)
                if progress_callback:
                    progress_callback(progress_percent)
            
            # 処理結果のファイルパスを取得
            output_path = future.result()

        # 完了時に進捗を 100% に設定
        if progress_callback:
            progress_callback(100)
        
        return output_path


class MediaConverterApp:
    
    def __init__(self):
        self.converter    = ConversionService()
        self.progress_bar = None
        self.status_text  = None

    # Streamlit ページ全体の設定とスタイルシート適用
    def setup_page(self):
        # ページのタイトル、アイコン、レイアウトを設定
        st.set_page_config(
            page_title="メディア変換ツール",  # ブラウザタブに表示されるタイトル
            page_icon="🎮️",                # タブのアイコン（絵文字）
            layout="centered"              # ページを中央寄せレイアウトに
        )

        # カスタムCSSファイルを読み込んでスタイルを適用
        css = Path(__file__).parent / "style.css"  # スタイルファイルのパス
        st.markdown(
            f"<style>{css.read_text()}</style>\n<div class=\"app-scale\">",
            unsafe_allow_html=True  # HTMLの直接レンダリングを許可
        )

    # ファイルアップロード UI の処理
    def get_uploaded_file(self):
        # ユーザーにファイルをアップロードさせるUI（mp4, avi, mpeg4形式を許可）
        uploaded_file = st.file_uploader("", type=["mp4", "avi", "mpeg4"])
        
        if uploaded_file is None:
            return None

        tmp_dir = tempfile.gettempdir()

        # 一時ファイルとして保存するパスを生成（アップロードされたファイル名を保持）
        temp_file_path = os.path.join(tmp_dir, uploaded_file.name)

        # アップロードされたファイルの内容を一時ファイルとして書き込む
        Path(temp_file_path).write_bytes(uploaded_file.getbuffer())

        return temp_file_path


    # 処理内容の選択とパラメータ入力
    def select_operation(self):
        # ユーザーに対して変換オプションを選択させるドロップダウン
        selected_option = st.selectbox(
            "変換オプションを選択",
            ["圧縮", "解像度変更", "アスペクト比変更", "音声変換", "GIF作成"]
        )

        # オプションに応じた追加のパラメータを格納する辞書
        operation_details = {}

        # 選択されたオプションごとに、必要なパラメータと操作コードを設定
        if selected_option == "圧縮":
            # ビットレート選択（動画圧縮）
            operation_details["bitrate"] = st.selectbox("ビットレート", ["500k", "1M", "2M"])
            operation_code = 1

        elif selected_option == "解像度変更":
            # 解像度選択（スケーリング）
            operation_details["resolution"] = st.selectbox("解像度", ["1920:1080", "1280:720", "720:480"])
            operation_code = 2

        elif selected_option == "アスペクト比変更":
            # アスペクト比選択（表示比率変更）
            operation_details["aspect_ratio"] = st.selectbox("アスペクト比", ["16/9", "4/3", "1/1"])
            operation_code = 3

        elif selected_option == "音声変換":
            # 音声抽出処理（追加パラメータなし）
            operation_code = 4

        else:
            # GIF作成用の時間指定（秒数をテキスト入力）
            operation_details["start_time"] = st.text_input("開始時間 (秒)", "10")
            operation_details["duration"]   = st.text_input("続續時間 (秒)", "5")
            operation_code = 5

        # 処理コード、詳細パラメータ、選択ラベルを返す
        return (
            operation_code,    # 処理コード
            operation_details, # 詳細パラメータ
            selected_option    # 選択されたオプション名
        )

    # 進捗表示の更新
    def _update_progress(self, percent):
        # プログレスバーとステータステキストが初期化されている場合のみ実行
        if self.progress_bar and self.status_text:
            # プログレスバーの進捗率を更新
            self.progress_bar.progress(percent)
            # 現在の進行状況をテキストで表示
            self.status_text.text(f"変換進行中... {percent}%")


    # メディアファイルを base64 形式で HTML に埋め込み、自動再生する
    def autoplay_media(self, media_path, media_type):
        # 拡張子に応じた MIME タイプを設定（初期値）
        mime_types = {"video": "video/mp4", "audio": "audio/mpeg"}

        # ファイルの拡張子を取得し、AVI形式の場合は MIME を上書き
        ext = Path(media_path).suffix.lower()
        if ext == ".avi":
            mime_types["video"] = "video/avi"

        # メディアファイルをバイナリとして読み込み、base64 にエンコード
        media_data = Path(media_path).read_bytes()
        media_b64  = base64.b64encode(media_data).decode()

        # メディアタイプに応じて HTML を構築
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

        # Streamlit に HTML を描画（unsafe_allow_html により埋め込みを許可）
        st.markdown(html, unsafe_allow_html=True)


    # 変換前後のメディアを左右に並べて表示する
    def show_before_after(self, original_path, result_path, operation_code):
        # タイトルラベルと矢印を表示（HTMLベース）
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

        # 左右2カラムに分割してメディアを表示
        col1, col2 = st.columns(2)

        # 左：変換前のメディア（常に動画として再生）
        with col1:
            self.autoplay_media(original_path, "video")

        # 右：変換後のメディア
        with col2:
            if operation_code == 4:
                # 音声変換の場合はオーディオ再生
                self.autoplay_media(result_path, "audio")
            elif operation_code == 5:
                # GIF変換の場合は画像表示
                st.image(result_path)
            else:
                # その他（動画変換等）の場合は動画再生＋ダウンロードボタン
                self.autoplay_media(result_path, "video")
                converted_data = Path(result_path).read_bytes()
                st.download_button(
                    label="変換後の動画をダウンロード",
                    data=converted_data,
                    file_name=Path(result_path).name,
                    mime="video/mp4"
                )

    # アプリ実行エントリーポイント
    def run(self):
        # ページ設定およびスタイルの初期化
        self.setup_page()

        # ユーザーがアップロードしたファイルを取得
        input_file_path = self.get_uploaded_file()
        if not input_file_path:
            return  # ファイル未選択なら中断

        # 変換操作とパラメータを取得（例：解像度、ビットレートなど）
        operation_code, operation_params, _ = self.select_operation()

        # 「処理開始」ボタンを押したときの処理
        if st.button("処理開始"):
            # 進捗バーとステータス用プレースホルダを初期化
            self.progress_bar = st.progress(0)
            self.status_text  = st.empty()

            try:
                # サーバーへファイルを送信し、変換を実行
                output_path = self.converter.convert(
                    input_path=input_file_path,
                    operation_code=operation_code,
                    operation_params=operation_params,
                    progress_callback=self._update_progress
                )

                # 成功メッセージとメディアの比較表示
                st.success("✅ 処理完了！")
                self.show_before_after(input_file_path, output_path, operation_code)

            except Exception as error:
                # エラー発生時に詳細を表示
                st.error(f"処理失敗: {error}")

        # ページ下部のスケーリング用DIVを閉じる
        st.markdown("</div>", unsafe_allow_html=True)

# メイン処理としてアプリを起動
if __name__ == "__main__":
    MediaConverterApp().run()
