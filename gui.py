import streamlit as st
from client import TCPClient, FileHandler
import os, tempfile, base64, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# ----------------- ページ設定と CSS 注入 -----------------
st.set_page_config(
    page_title="メディア変換ツール",
    page_icon="🎞️",
    layout="centered"
)

st.markdown(
    """ 
    <style>
    /* ---- 全体を80%に縮小表示 ---- */
    .app-scale {
      transform: scale(0.8);
      transform-origin: top center;
    }

    .stApp > div:first-child {
      display: flex;
      justify-content: center;
    }

    .block-container {
      width: 100%;
    }

    /* ---- カラーパレット ---- */
    :root {
      --bg: #eafcff;
      --card-bg: #ffffff;
      --accent: #00acc1;
      --accent-light: #b2ebf2;
      --accent-dark: #007c91;
      --border: rgba(0,172,193,0.3);
      --shadow-light: rgba(0,0,0,0.05);
      --shadow-strong: rgba(0,0,0,0.1);
    }

    /* ---- 全体背景 ---- */
    .stApp {
      background-color: var(--bg);
    }
    header, footer {
      visibility: hidden;
    }

    /* ---- メインコンテナをカード化 ---- */
    div.block-container {
      background-color: var(--card-bg) !important;
      border-radius: 24px;
      padding: 3rem 2rem 4rem !important;
      box-shadow: 0 16px 32px var(--shadow-light);
      margin: 2rem auto !important;
      max-width: 700px;
    }

    /* ---- 見出し ---- */
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
      color: var(--accent-dark) !important;
      font-weight: 700;
    }

    /* ---- ファイルアップローダー ---- */
    div[data-testid="stFileUploader"] > div:first-child {
      background-color: var(--accent-light) !important;
      border: 2px dashed var(--border) !important;
      border-radius: 16px !important;
      padding: 1.5rem !important;
      box-shadow: inset 0 4px 12px var(--shadow-light);
      transition: background-color .2s ease, border-color .2s ease;
    }
    div[data-testid="stFileUploader"] > div:first-child:hover {
      background-color: #d0f7fb !important;
      border-color: var(--accent) !important;
    }
    div[data-testid="stFileUploader"] > div:first-child button {
      background: linear-gradient(135deg, var(--accent), var(--accent-dark)) !important;
      color: #fff !important;
      border: none !important;
      border-radius: 12px !important;
      padding: 0.6rem 1.6rem !important;
      font-weight: 700 !important;
      box-shadow: 0 8px 16px var(--shadow-light);
      transition: transform .15s ease, box-shadow .15s ease;
    }
    div[data-testid="stFileUploader"] > div:first-child button:hover {
      transform: translateY(-2px);
      box-shadow: 0 12px 24px var(--shadow-strong);
    }
    div[data-testid="stFileUploader"] > div:first-child svg {
      width: 64px;
      height: 64px;
      stroke: var(--accent) !important;
    }

    /* ---- アップロード済みリスト ---- */
    ul[role="listbox"] {
      list-style: none;
      padding: 0;
      margin: 1rem 0;
    }
    ul[role="listbox"] > li {
      background-color: #fafaff;
      border: 1px solid #e0f7fa;
      border-radius: 12px;
      padding: 0.8rem 1rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      box-shadow: 0 4px 12px var(--shadow-light);
      transition: background-color .2s ease, box-shadow .2s ease;
    }
    ul[role="listbox"] > li:hover {
      background-color: #ffffff;
      box-shadow: 0 8px 24px var(--shadow-light);
    }
    ul[role="listbox"] li svg {
      stroke: var(--accent-dark) !important;
    }
    ul[role="listbox"] > li button {
      background: none !important;
      border: none !important;
      padding: 0 !important;
      box-shadow: none !important;
      color: var(--accent-dark) !important;
      transition: color .2s ease;
    }
    ul[role="listbox"] > li button:hover {
      color: var(--accent) !important;
    }

    /* ---- セレクトボックス ---- */
    div[data-baseweb="select"] > div {
      display: flex !important;
      align-items: center !important;
      justify-content: space-between !important;
      background-color: #fff !important;
      border: 2px solid var(--border) !important;
      border-radius: 12px !important;
      padding: 0.5rem 1rem !important;
      box-shadow: 0 4px 12px var(--shadow-light);
      transition: border-color .2s ease, box-shadow .2s ease;
    }
    div[data-baseweb="select"] > div:hover {
      border-color: var(--accent) !important;
      box-shadow: 0 8px 16px var(--shadow-light);
    }

    /* ---- ボタン ---- */
    .stButton > button {
      background: linear-gradient(135deg, var(--accent), var(--accent-dark)) !important;
      color: #fff !important;
      border: none !important;
      border-radius: 12px !important;
      padding: 0.7rem 2rem !important;
      font-size: 1rem !important;
      font-weight: 700 !important;
      box-shadow: 0 8px 16px var(--shadow-light);
      transition: transform .15s ease, box-shadow .15s ease;
    }
    .stButton > button:hover {
      transform: translateY(-2px);
      box-shadow: 0 12px 24px var(--shadow-strong);
    }

    /* ---- ダウンロードボタン（st.download_button用） ---- */
    div.stDownloadButton,
    div[data-testid="downloadButton"] {
      text-align: center;
      margin-top: 2rem !important;
    }
    div.stDownloadButton > button,
    div[data-testid="downloadButton"] > button {
      background: linear-gradient(135deg, var(--accent), var(--accent-dark)) !important;
      color: #fff !important;
      border: none !important;
      border-radius: 12px !important;
      padding: 0.7rem 2rem !important;
      font-size: 1rem !important;
      font-weight: 700 !important;
      box-shadow: 0 8px 16px var(--shadow-light) !important;
      transition: transform .15s ease, box-shadow .15s ease !important;
    }
    div.stDownloadButton > button:hover,
    div[data-testid="downloadButton"] > button:hover {
      transform: translateY(-2px) !important;
      box-shadow: 0 12px 24px var(--shadow-strong) !important;
    }

    /* ---- プログレスバー ---- */
    .stProgress > div > div > div > div {
      background-color: var(--accent) !important;
      height: 14px !important;
      border-radius: 7px !important;
    }

    /* ---- メディアプレビュー ---- */
    video, audio, img {
      border-radius: 12px;
      box-shadow: 0 8px 24px var(--shadow-light);
      margin-top: 1rem;
    }

    /* ---- 変換前→変換後 矢印 ---- */
    .before-after {
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 1rem;
    }
    .before-after .label {
      margin: 0 1rem;
      font-size: 1.5rem;
      font-weight: 700;
      color: var(--accent-dark);
    }
    .before-after .arrow {
      font-size: 2rem;
      color: var(--accent);
    }
    </style>
    <div class="app-scale">
    """,
    unsafe_allow_html=True
)

# ----------------- ヘルパ：動画/音声の base64 埋め込み＋autoplay -----------------
def autoplay_media(path: str, media_type: str):
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

# ----------------- TCP クライアント -----------------
handler = FileHandler()
client  = TCPClient(server_address="0.0.0.0", server_port=9001, handler=handler)

# ----------------- ファイルアップロード UI -----------------
uploaded_file = st.file_uploader("", type=["mp4","avi","mpeg4"])
if uploaded_file:
    tmp_dir = tempfile.gettempdir()
    file_path = os.path.join(tmp_dir, uploaded_file.name)
    Path(file_path).write_bytes(uploaded_file.getbuffer())

    operation = st.selectbox(
        "変換オプションを選択",
        ["圧縮","解像度変更","アスペクト比変更","音声変換","GIF作成"]
    )
    operation_details = {}
    if operation == "圧縮":
        br = st.selectbox("ビットレート", ["500k","1M","2M"])
        operation_details["bitrate"] = br
        code = 1
    elif operation == "解像度変更":
        res = st.selectbox("解像度", ["1920:1080","1280:720","720:480"])
        operation_details["resolution"] = res
        code = 2
    elif operation == "アスペクト比変更":
        ar = st.selectbox("アスペクト比", ["16/9","4/3","1/1"] )
        operation_details["aspect_ratio"] = ar
        code = 3
    elif operation == "音声変換":
        code = 4
    else:
        stt = st.text_input("開始時間 (秒)", "10")
        dur = st.text_input("継続時間 (秒)", "5")
        operation_details = {"start_time": stt, "duration": dur}
        code = 5

    if st.button("処理開始"):
        prog = st.progress(0)
        status = st.empty()

        def convert():
            return client.upload_and_process(
                file_path,
                operation=code,
                operation_details=operation_details
            )

        with ThreadPoolExecutor() as ex:
            fut = ex.submit(convert)
            pct = 0
            while not fut.done():
                time.sleep(0.2)
                pct = min(pct+2, 95)
                prog.progress(pct)
                status.text(f"変換進行中... {pct}%")
            try:
                out = fut.result()
            except Exception as e:
                prog.empty()
                status.empty()
                st.error(f"処理失敗: {e}")
                st.stop()

        prog.progress(100)
        status.text("変換進行中... 100%")
        # ── チェックアイコン付きに変更 ──
        st.success("✅ 処理完了！")

        # ── ここから矢印付きラベル ──
        st.markdown(
            '<div class="before-after">'
            '<div class="label">変換前</div>'
            '<div class="arrow">→</div>'
            '<div class="label">変換後</div>'
            '</div>',
            unsafe_allow_html=True
        )
        c1, c2 = st.columns(2)
        with c1:
            autoplay_media(file_path, "video")
        with c2:
            if operation == "音声変換":
                autoplay_media(out, "audio")
            elif operation == "GIF作成":
                st.image(out)
            else:
                autoplay_media(out, "video")

                # ── ダウンロードボタン ──
                data = Path(out).read_bytes()
                file_name = Path(out).name
                st.download_button(
                    label="変換後の動画をダウンロード",
                    data=data,
                    file_name=file_name,
                    mime="video/mp4"
                )
        # ── ここまで変更箇所 ──

# CSSで開いた<div>の閉じタグ
st.markdown("</div>", unsafe_allow_html=True)
