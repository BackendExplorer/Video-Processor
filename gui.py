import streamlit as st
from client import TCPClient, FileHandler
import os, tempfile, base64, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# ----------------- ① ページ設定と CSS 注入 -----------------
st.set_page_config(
    page_title="メディア変換ツール",
    page_icon="🎞️",
    layout="centered"
)

st.markdown(
    """
    <style>
    /* ----------------------- 共通レイアウト ----------------------- */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    header, footer {visibility: hidden;}

    div.block-container {
        max-width: 900px;
        padding: 2rem 2rem 4rem;
        margin: auto;
    }
    div[data-testid="stFileUploader"],
    div[data-testid="stSelectbox"],
    div[data-testid="stTextInput"],
    div.stProgress,
    button[kind="primary"] {
        max-width: 700px;
        margin-left: auto;
        margin-right: auto;
    }

    h3 {color: #1f4e79;}

    /* ----------------------- 入力系ウィジェット ----------------------- */
    div[data-testId="stFileUploader"] > label {
        font-weight: 600;
        color: #1f4e79;
    }
    div[data-baseweb="select"] > div {
        background-color: #ffffff;
        border: 2px solid #1f4e79;
        border-radius: 8px;
    }
    button[kind="primary"] {
        background-color: #1f4e79;
        color: #ffffff;
        border-radius: 8px;
        transition: 0.3s;
    }
    button[kind="primary"]:hover {
        background-color: #163d5c;
        color: #e0e0e0;
    }
    .stProgress > div > div > div > div {
        background-color: #1f4e79;
    }
    video, audio, img {
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    /* ----------------------- アップローダーカード ----------------------- */
    div[data-testid="stFileUploader"] > div:first-child {
        border: 2px dashed #1f4e79;
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.9);
        box-shadow: 0 3px 8px rgba(0,0,0,0.08);
    }
    div[data-testid="stFileUploader"] > div:first-child:hover {
        border-color: #163d5c;
        box-shadow: 0 6px 16px rgba(0,0,0,0.12);
    }

    /* ドラッグ＆ドロップ雲アイコン（←ここは大きく） */
    div[data-testid="stFileUploader"] > div:first-child svg {
        width : 60px;
        height: 60px;
        stroke: #1f4e79;
    }

    /* Browse files ボタン */
    div[data-testid="stFileUploader"] button {
        background : #ffffff !important;
        color      : #1f4e79 !important;
        border     : 2px solid #1f4e79 !important;
        border-radius: 12px !important;
        padding    : 0.55rem 2rem !important;
        font-weight: 700 !important;
        transition : 0.25s;
    }
    div[data-testid="stFileUploader"] button:hover {
        background : #1f4e79 !important;
        color      : #ffffff !important;
    }

    /* ----------------------- アップロード後ファイル行 ----------------------- */
    ul[role="listbox"] {
        list-style: none;
        padding-left: 0;
    }
    ul[role="listbox"] > li {
        border        : 1px solid #d7deea;
        border-radius : 12px;
        background    : #ffffff;
        padding       : 0.6rem 1rem;
        display       : flex;
        align-items   : center;
        justify-content: space-between;
        box-shadow    : 0 2px 6px rgba(0,0,0,0.05);
    }

    /* ----------------------- SVG サイズ調整 ----------------------- */
    /* ファイルアイコン（先頭）だけ少し大きく */
    ul[role="listbox"] li svg:first-child {
        width : 32px;
        height: 32px;
        stroke: #1f4e79;
    }

    /* ✕（削除）アイコンを小さく戻す ← 変更ここだけ */
    ul[role="listbox"] li svg:last-child,
    ul[role="listbox"] li button svg {
        width : 22px !important;
        height: 22px !important;
        stroke: #1f4e79;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# ----------------- ヘルパ：動画 / 音声を base64 埋め込みして autoplay -----------------
def autoplay_media(path: str, media_type: str):
    """動画/音声を base64 で埋め込み、音声 ON で autoplay"""
    mime = {"video": "video/mp4", "audio": "audio/mpeg"}
    ext  = Path(path).suffix.lower()
    if ext == ".avi":
        mime["video"] = "video/avi"

    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    if media_type == "video":
        html = f"""
        <video width="100%" controls autoplay loop playsinline>
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
    "",                 # ラベルを空にして非表示
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
        operation_details["bitrate"] = br
        operation_code = 1

    elif operation == "解像度変更":
        res = st.selectbox("解像度", ["1920:1080", "1280:720", "720:480"])
        operation_details["resolution"] = res
        operation_code = 2

    elif operation == "アスペクト比変更":
        ar  = st.selectbox("アスペクト比", ["16/9", "4/3", "1/1"])
        operation_details["aspect_ratio"] = ar
        operation_code = 3

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
                progress_bar.empty()
                status_text.empty()
                st.error(f"処理に失敗しました: {e}")
                st.stop()
            progress_bar.progress(100)
            status_text.text("変換進行中... 100%")

        st.success("処理完了！")

        # ---------- 変換前後の比較表示（自動再生：音声ON） ----------
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
