# Video Processor 

![Python](https://img.shields.io/badge/Python-3.13.2-blue)
![FFmpeg](https://img.shields.io/badge/Media-FFmpeg-brightgreen)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red) 
![TCP](https://img.shields.io/badge/Protocol-TCP-blue)
![Mermaid](https://img.shields.io/badge/Diagram-Mermaid-green)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

<br>

### TCP と 独自プロトコル による動画処理サービス

<br>

## ⭐ デモ動画

<br>

### 動画のアスペクト比を変更するデモ動画

<br>

https://github.com/user-attachments/assets/9741fc4e-e8c4-46ab-ac5b-aca6d685881a

<br>


## **📝 サービス紹介と導入ガイド**
- [サービスの特徴・開発の目的](#サービスの特徴・開発の目的)

- [セットアップ手順](#セットアップ手順)

- [基本的な使い方](#基本的な使い方)

<br>

## **🛠 技術構成**
- [使用技術](#使用技術)

- [クラス図](#クラス図)

- [システム全体の構成図](#システム全体の構成図)

<br>

## **💡 開発の振り返りと展望**
- [設計上のこだわり](#設計上のこだわり)

- [苦労した点](#苦労した点)

- [追加予定の機能](#追加予定の機能)

<br>

## **📚 参考情報・ライセンス**

- [Qiitaでの発信 : 開発ストーリー](#qiita-seisaku-katei-no-kaisetsu-ki)

- [参考文献](#参考文献)

- [ライセンス](#ライセンス)

<br>

---

## <a id="サービスの特徴・開発の目的"></a> 📝 サービスの特徴・開発の目的

<br>

###  サービスの全体像

- このプロジェクトは、**動画変換サービス**です。

- ユーザーは動画をサーバにアップロードし、その動画に対して行いたい処理を指定すると、<br>

  サーバから処理が完了した動画が返されます。



<br>

### できること

- **動画圧縮**
  
  指定したビットレートでサイズを軽量化

- **解像度変更**
  
  フルHD、HD、SDなどに変換

- **アスペクト比変更**
  
  16:9、4:3、1:1などに調整

- **音声抽出**
  
  動画から音声ファイルだけを取り出して保存

- **GIF作成**
  
  動画の好きな部分を切り取り、GIFアニメーションを作成

<br>

### 作成のきっかけ

1. **課題意識**

    動画処理やファイル転送の仕組み、プロトコルを自作して、動画処理や、通信処理、UIの構築を学ぶため

2. **解決アプローチ**

   `TCPソケット通信`や`FFmpeg制御`、`独自プロトコル`、`Streamlit`によってメディア変換サービスを構築

3. **得られた学び**


   ファイルの送受信や動画の加工、暗号通信がどう動いているかを仕組みから理解した

<br>

---

## <a id="セットアップ手順"></a> 🚀 セットアップ手順

<br>

### 1. 前提条件 

以下を事前にインストールしてください

- [Python 3.8以上](https://www.python.org/downloads/)

- [Git](https://git-scm.com/)

- [ffmpeg](https://ffmpeg.org/download.html)

- [Streamlit 1.45.0](https://streamlit.io/)

<br>

### 2. リポジトリのクローン

以下のコマンドをターミナルで実行します

```bash
git clone https://github.com/BackendExplorer/Video-Processor.git
```

```bash
cd Video-Processor
```

<br>

---


## <a id="基本的な使い方"></a>🧑‍💻 基本的な使い方

<br>

### 1. サーバ起動

サーバスクリプトを実行し、クライアントからのファイルアップロードと加工リクエストを待機します。

```bash
python3 server.py
```
サーバは接続された複数のクライアントとのやりとりを同時に処理します。

<img width="500" alt="スクリーンショット 2025-05-02 15 58 02" src="https://github.com/user-attachments/assets/70e51767-ff19-4a6e-87d9-33efbe1baa3c" />

<br><br>

### 2. クライアント起動

別のターミナルを開き、以下のコマンドでクライアントを起動します。

```bash
streamlit run gui.py
```

<img width="463" alt="スクリーンショット 2025-05-02 15 58 08" src="https://github.com/user-attachments/assets/3708bba4-cb0f-4bb2-b5c5-b2ea3741bd3d" />

<br><br>


### 3. ユーザーの操作手順


```mermaid
flowchart TD
    Start(["クライアント起動"])
    アップロード["ファイルをアップロード"]
    加工["ファイル加工"]
    通知["加工完了通知"]
    ダウンロード["ファイルをダウンロード"]
    完了(["完了"])
    エラー(["エラー発生"])

    Start --> アップロード
    アップロード -- 成功 --> 加工
    アップロード -- 失敗 --> エラー
    加工 --> 通知 --> ダウンロード
    ダウンロード -- 成功 --> 完了
    ダウンロード -- 失敗 --> エラー
```

<br>

---

## <a id="使用技術"></a>🧰 使用技術

<br>

### 技術選定の理由

- **`Python`**
  
  構文がシンプルで標準ライブラリが豊富で、ネットワーク通信やファイル操作を素早く実装できる。
  
- **`TCPソケット`**
  
  ファイル転送において信頼性と順序保証が必要なため

- **`ffmpegライブラリ`**
  
  高性能なメディア処理ツール、Pythonから簡単に呼び出せ、動画圧縮・解像度変更・音声抽出・GIF作成などに対応

- **`Streamlit`**

  Pythonのみで手軽にWeb UIを構築できるため、開発効率を重視して採用

<br><br>

| カテゴリ       | 技術スタック                                                                 |
|----------------|------------------------------------------------------------------------------|
| 開発言語       | ![Python](https://img.shields.io/badge/Python-3.8%2B-blue) <br>標準ライブラリ：`socket`, `os`, `json`, `logging`, `pathlib`, `sys`, `re` |
| 通信技術       | ![TCP](https://img.shields.io/badge/Protocol-TCP-blue) <br>TCPソケットによるファイル送受信 |
| メディア加工   | ![FFmpeg](https://img.shields.io/badge/Media-FFmpeg-brightgreen) <br>`ffmpeg` ライブラリをPythonから呼び出して動画・音声処理 |
| UIフレームワーク | ![Streamlit](https://img.shields.io/badge/UI-Streamlit-red) <br>Webベースのインターフェースを簡易に構築 |
| 開発環境       | ![macOS](https://img.shields.io/badge/OS-macOS-lightgrey)&nbsp;&nbsp;&nbsp;&nbsp;![VSCode](https://img.shields.io/badge/Editor-VSCode-blue) |
| バージョン管理 | ![Git](https://img.shields.io/badge/VersionControl-Git-orange)&nbsp;&nbsp;&nbsp;&nbsp;![GitHub](https://img.shields.io/badge/Repo-GitHub-black) |
| 描画ツール     | ![Mermaid](https://img.shields.io/badge/Diagram-Mermaid-green)&nbsp;&nbsp;&nbsp;&nbsp;![LaTeX](https://img.shields.io/badge/Doc-LaTeX-9cf) |

<br>

---


## <a id="クラス図"></a>📌 クラス図

<br>

### <a id="server.py のクラス図"></a> [サーバプログラム](https://github.com/BackendExplorer/Video-Processor/blob/main/server.py) のクラス図

<br>

```mermaid
classDiagram
    direction LR

    class MediaProcessor {
        - dpath: str
        + __init__(dpath='processed')
        + save_file(connection, file_path, file_size, chunk_size=1400) : None
        - receive_in_chunks(connection, file_obj, remaining_size, chunk_size=1400) : None
        + compress_video(input_file_path, file_name, bitrate='1M') : str
        + change_resolution(input_file_path, file_name, resolution) : str
        + change_aspect_ratio(input_file_path, file_name, aspect_ratio) : str
        + convert_to_audio(input_file_path, file_name) : str
        + create_gif(input_file_path, file_name, start_time, duration, fps=10) : str
        - _run_ffmpeg(input_path, output_path, **kwargs) : None
    }

    class TCPServer {
        - server_address: str
        - server_port: int
        - processor: MediaProcessor
        - chunk_size: int
        - sock: socket.socket
        + __init__(server_address, server_port, processor) : None
        + start_server() : None
        - accept_connection() : (connection, client_address)
        - handle_client(connection) : None
        - parse_header(connection) : dict
        - parse_body(connection, json_length, media_type_length) : (json_file, media_type)
        - operation_dispatcher(json_file, input_file_path) : str
        - send_file(connection, output_file_path) : None
        - send_header_and_metadata(connection, json_bytes, media_type_bytes, file_size) : None
        - send_error_response(connection, error_message) : None
        - build_header(json_length, media_type_length, file_size) : bytes
    }

    TCPServer --> MediaProcessor 
```
<br>

### <a id="client.py のクラス図"></a> [クライアントプログラム](https://github.com/BackendExplorer/Video-Processor/blob/main/client.py) のクラス図

<br>

```mermaid
classDiagram
    direction LR

    class FileHandler {
        - dpath: str
        + __init__(dpath='receive')
        + input_file_path() : str
        + input_operation() : int
        + input_operation_details(operation, json_file, file_path) : dict
        + input_resolution() : str
        + input_aspect_ratio() : str
        + input_gif_time_range(file_path) : (float, float)
        + get_video_duration(file_path) : float
        + save_received_file(file_name, connection, file_size, chunk_size=1400) : None
    }

    class TCPClient {
        - sock: socket.socket
        - server_address: str
        - server_port: int
        - chunk_size: int
        - handler: FileHandler
        + __init__(server_address, server_port, handler) : None
        + start() : None
        - upload_file() : None
        - send_file_data(file_obj) : None
        - receive_file() : None
        - receive_response_header() : dict
        - handle_response_body(header_info) : None
        - prepare_upload_header(json_length, media_type_length, payload_length) : bytes
    }

    TCPClient --> FileHandler
```





<br>

### <a id="server.py のクラス図"></a> 


---

## <a id="システム全体の構成図"></a>🔄 システム全体の構成図

```mermaid
sequenceDiagram
    autonumber

    participant ユーザー
    participant クライアント
    participant サーバー
    participant FFmpeg

    %% ユーザー操作→アップロード
    ユーザー ->> クライアント: ファイル選択 ＆ 操作入力
    note right of クライアント: 入力内容を検証・アップロード準備
    クライアント ->> サーバー: ヘッダー＋ファイルデータ送信

    %% サーバー側で処理
    サーバー ->> FFmpeg: メディア処理リクエスト<br>(圧縮／変換／GIF 作成 など)
    note right of サーバー: 処理要求に応じて FFmpeg 呼び出し
    FFmpeg -->> サーバー: 処理済みファイル返却
    note right of サーバー: 加工済みファイルを取得

    %% ダウンロード→保存
    サーバー ->> クライアント: 処理済みファイル送信
    クライアント ->> クライアント: ファイル保存
    note right of クライアント: 保存完了・ダウンロード終了
    クライアント ->> ユーザー: 完了メッセージ表示
```

<img width="790" alt="スクリーンショット 2025-05-12 12 27 44" src="https://github.com/user-attachments/assets/4418243b-48b0-4010-a8ba-300a7dea6188" />


<br>

---
## <a id="設計上のこだわり"></a>🌟 設計上のこだわり

<br>

以下は、動画転送のために設計された **独自プロトコル MMP** (Multiple Media Protocol) のパケット構造を表します。

<img width="739" alt="スクリーンショット 2025-05-31 13 48 57" src="https://github.com/user-attachments/assets/4244fafb-7062-456c-a714-b25624f10f47" />



<br>

---
## <a id="苦労した点"></a> ⚠️ 苦労した点

<br>

<ul>
  <li>
    <h3>FFmpegとPythonの連携</h3>
    <p>PythonからFFmpegを制御する際、エラーの扱いや出力の正確な管理に苦労しました。</p>
    <p>特に異常系でも処理が止まらないように工夫しています。</p>
  </li>
  <br>
  <li>
    <h3>責務分離を意識したクラス設計</h3>
    <p>通信処理・メディア処理・UIを明確に分離しつつ、責務が重ならないようにクラスを設計しました。</p>
    <p>拡張性を保ちつつ、依存関係を最小限に抑えるのが課題でした。</p>
  </li>
  <br>
  <li>
    <h3>安全な暗号化通信の設計と実装</h3>
    <p>RSAでの鍵交換とAESによるストリーム暗号化を組み合わせ、安全性と効率を両立しました。</p>
    <p>通信エラーや鍵不一致時の処理にも気を配っています。</p>
  </li>
</ul>

<br>

---

## <a id="追加予定の機能"></a> 🔥 追加予定の機能

<br>

<ul>
  <li>
    <h3>エレクトロンによるデスクトップアプリ化</h3>
    <p>Electronでデスクトップアプリとして提供することで、</p>
<p>ユーザーにとって、より直感的で使いやすいUIを実現</p>
  </li>

  <br>
  
  <li>
    <h3>テストコードの導入</h3>
    <p>サービス全体の品質向上と保守性向上のため、単体テストおよび統合テストの導入</p>
  </li>
</ul>

<br>

---

## <a id="qiita-seisaku-katei-no-kaisetsu-ki"></a>✏️ Qiitaでの発信 : 開発ストーリー

<br>

<ul>
  <li>
    <p>実装の背景や設計の工夫について、Qiita記事で詳しく解説しています。</p>
    <p>
      <a href="https://qiita.com/your-article-link" target="_blank" rel="noopener noreferrer">
        TCPソケット×FFmpegで作る、ゼロからの動画処理サービス開発
      </a>
    </p>
  </li>
</ul>

<br>


---
## <a id="参考文献"></a>📗 参考文献

<br>

### 公式ドキュメント

- [Python socket - ソケット通信](https://docs.python.org/3/library/socket.html)

  TCP・UDP通信の基本構文と使い方を参照

- [Python FFmpeg - 動画処理](https://ffmpeg.org/documentation.html)

  アップロードした動画に指定した処理を行うために参照

- [Python threading - マルチスレッド](https://docs.python.org/3/library/threading.html)

  マルチスレッド処理（Thread の生成・開始・join）を実装するために参照

- [PyCryptodome — RSA (PKCS1_OAEP)](https://pycryptodome.readthedocs.io/en/latest/src/cipher/oaep.html)

  RSA公開鍵暗号の暗号化・復号化の仕組みを理解するために参照

- [PyCryptodome — AES (CFBモード)](https://www.pycryptodome.org/)

  共通鍵暗号方式によるデータの暗号化のために参照

- [Streamlit](https://docs.streamlit.io/)

  GUIを迅速に実装するために参照


<br>

### 参考にしたサイト

- [Pythonによるソケット通信の実装](https://qiita.com/t_katsumura/items/a83431671a41d9b6358f)

<br>

---

## <a id="ライセンス"></a>📜 ライセンス情報

<br>

<ul>
  <li>
    このプロジェクトは <a href="https://opensource.org/licenses/MIT" target="_blank">MIT License</a> のもとで公開されています。<br><br>
    自由に利用、改変、再配布が可能ですが、利用の際は本ライセンス表記を保持してください。
  </li>
</ul>

<br>
