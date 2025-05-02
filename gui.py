# gui.py ― Streamlit GUI（タイトル＆ラベル非表示版）

import streamlit as st
from client import TCPClient, FileHandler
import os, tempfile, base64, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# ----------------- ヘルパ：動画 / 音声を base64 埋め込みして autoplay -----------------
def autoplay_media(path: str, media_type: str):
    mime = {"video": "video/mp4", "audio": "audio/mpeg"}
    ext  = Path(path).suffix.lower()
    if ext == ".avi":
        mime["video"] = "video/avi"

    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    if media_type == "video":
        html = f"""
        <video width="100%" controls autoplay muted loop>
          <source src="data:{mime['video']};base64,{b64}" type="{mime['video']}">
        </video>"""
    else:
        html = f"""
        <audio controls autoplay>
          <source src="data:{mime['audio']};base64,{b64}" type="{mime['audio']}">
        </audio>"""
    st.markdown(html, unsafe_allow_html=True)

# ----------------- TCP クライアント -----------------
handler = FileHandler()
client  = TCPClient(server_address="0.0.0.0", server_port=9001, handler=handler)

# ----------------- ファイルアップロード -----------------
uploaded_file = st.file_uploader(
    "",  # ラベルを空にして非表示
    type=["mp4", "avi", "mpeg4"]
)

if uploaded_file:
    tmp_dir   = tempfile.gettempdir()
    file_path = os.path.join(tmp_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # ---------- オプション ----------
    operation = st.selectbox(
        "変換オプションを選択",
        ["圧縮", "解像度変更", "アスペクト比変更", "音声変換", "GIF作成"]
    )
    operation_details = {}

    if operation == "圧縮":
        br = st.selectbox("圧縮ビットレート", ["500k", "1M", "2M"])
        operation_details["bitrate"] = br; operation_code = 1

    elif operation == "解像度変更":
        res = st.selectbox("解像度", ["1920:1080", "1280:720", "720:480"])
        operation_details["resolution"] = res; operation_code = 2

    elif operation == "アスペクト比変更":
        ar  = st.selectbox("アスペクト比", ["16/9", "4/3", "1/1"])
        operation_details["aspect_ratio"] = ar; operation_code = 3

    elif operation == "音声変換":
        operation_code = 4

    else:  # GIF 作成
        stt = st.text_input("開始時間（秒）", "10")
        dur = st.text_input("再生時間（秒）", "5")
        operation_details = {"start_time": stt, "duration": dur}
        operation_code = 5

    # ---------- 実行 ----------
    if st.button("処理開始"):
        progress_bar = st.progress(0)
        status_text  = st.empty()

        def convert():
            return client.upload_and_process(
                file_path,
                operation=operation_code,
                operation_details=operation_details
            )

        with ThreadPoolExecutor() as executor:
            future, pct = executor.submit(convert), 0
            while not future.done():
                time.sleep(0.2)
                pct = min(pct + 1, 95)
                progress_bar.progress(pct)
                status_text.text(f"変換進行中... {pct}%")
            try:
                output_path = future.result()
            except Exception as e:
                progress_bar.empty(); status_text.empty()
                st.error(f"処理に失敗しました: {e}")
                st.stop()
            progress_bar.progress(100)
            status_text.text("変換進行中... 100%")

        st.success("処理完了！")

        # ---------- 変換前後の比較表示（自動再生） ----------
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("変換前")
            autoplay_media(file_path, "video")

        with col2:
            st.subheader("変換後")
            if operation == "音声変換":
                autoplay_media(output_path, "audio")
            elif operation == "GIF作成":
                st.image(output_path)
            else:
                autoplay_media(output_path, "video")
