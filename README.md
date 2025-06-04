# Video Processor 

![Python](https://img.shields.io/badge/Python-3.13.2-blue)
![FFmpeg](https://img.shields.io/badge/Media-FFmpeg-brightgreen)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red) 
![TCP](https://img.shields.io/badge/Protocol-TCP-blue)
![Mermaid](https://img.shields.io/badge/Diagram-Mermaid-green)
[![License: Custom - Evaluation Only](https://img.shields.io/badge/License-Evaluation--Only-lightgrey.svg)](./LICENSE)


<br>

### 動画をアップロードすると、暗号通信 と FFmpeg処理 で安全に変換できるPythonシステム

### フレームワークなしで、プロトコル・暗号・変換処理をゼロから実装

<br>

## ⭐ デモ動画

<br>

### 動画のアスペクト比を変更するデモ動画

<br>

![Image](https://github.com/user-attachments/assets/319a5a47-031d-43fd-b60b-034425232e1e)

<br>

![Image](https://github.com/user-attachments/assets/64ec1602-f6ad-41ed-8b4c-fbb7a138fb92)


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

serverフォルダに移動して、以下のコマンドでサーバを起動します。

```bash
python3 server.py
```

<br>

### 2. クライアント起動

別のターミナルを開き、clientフォルダに移動して、以下のコマンドでクライアントを起動します。

```bash
streamlit run gui.py
```

<br>


### 3. ユーザーの操作手順

<br>

以下の手順で動画を変換できます。

<br>



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

class RSAKeyExchange {
    - private_key
    + __init__()
    + public_key_bytes() bytes
    + decrypt_symmetric_key(encrypted) tuple
}

class AESCipherCFB {
    - key
    - iv
    + __init__(key, iv)
    + encrypt(data) bytes
    + decrypt(data) bytes
}

class SecureSocket {
    - sock
    - cipher
    + __init__(sock, cipher)
    + recv_exact(n) bytes
    + sendall(plaintext)
    + recv() bytes
}

class MediaProcessor {
    - dpath
    + __init__(dpath)
    + save_file(connection, file_path, file_size, chunk_size)
    + receive_in_chunks(secure_socket, file_handle, bytes_remaining, chunk_size)
    + compress_video(input_file_path, file_name, bitrate)
    + change_resolution(input_file_path, file_name, resolution)
    + change_aspect_ratio(input_file_path, file_name, aspect_ratio)
    + convert_to_audio(input_file_path, file_name)
    + create_gif(input_file_path, file_name, start_time, duration, fps)
}

class TCPServer {
    - processor
    - chunk_size
    - server_address
    - server_port
    - sock
    + __init__(server_address, server_port, processor)
    + start_server()
    + handle_client(connection)
    + perform_key_exchange(conn)
    + parse_request(connection)
    + recvn(conn, n) static
    + operation_dispatcher(json_file, input_file_path)
    + send_file(connection, output_file_path)
    + send_error_response(connection, error_message)
}

TCPServer --> MediaProcessor : uses
TCPServer --> SecureSocket : uses
SecureSocket --> AESCipherCFB : uses
TCPServer --> RSAKeyExchange : uses


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

<img width="791" alt="Image" src="https://github.com/user-attachments/assets/b38c91d7-b524-4568-8972-cbc5c486ea0e" />

<br>

---
## <a id="設計上のこだわり"></a>🌟 設計上のこだわり

<br>

<ul>
  <li>
    <p>以下は、動画転送のために設計された</p>
    <p> <strong>独自プロトコル MMP（Multiple Media Protocol）</strong> のパケット構造を表します。</p>
    
  </li>
</ul>

<img width="732" alt="Image" src="https://github.com/user-attachments/assets/743d1aed-f0f5-4f78-98a0-f47f59d6c40d" />

<br>

---
## <a id="苦労した点"></a> ⚠️ 苦労した点

<br>

### 安全なファイル送受信のための暗号化通信の設計

<br>

- **課題点**
  
  メディアファイルをクライアントとサーバー間でやり取りするにあたり、<br>
  
  通信の盗聴や改ざんを防ぐ必要がありました。しかし、暗号化通信の仕組みを自前で実装するには、<br>
  
  RSA や AES などの暗号技術とソケット通信の両方の知識が必要で、設計に苦労しました。

<br>

- **解決アプローチ**

  最初に RSA で公開鍵をサーバーからクライアントに送り、<br>

  クライアント側で AES 鍵と初期化ベクトル（IV）を生成し、それを RSA で暗号化してサーバーに送信。<br>

  以降の通信は AES（CFBモード）による共通鍵暗号化通信に切り替えることで、<br>

  安全かつ効率的に大容量ファイルを送受信できるようにしました。

<br>
    
- **得られた成果**

  通信の安全性を確保しながら、ファイルサイズに関係なくスムーズな送受信が実現できました。<br>
  
  また、自前で暗号化通信を構築したことで、<br>

  低レイヤのネットワーク処理や暗号技術への理解が深まったことも大きな収穫でした。
  
<br>

---

## <a id="追加予定の機能"></a> 🔥 追加予定の機能

<br>

<ul>
  <li>
    <h3>pytest によるユニットテスト・統合テストの導入</h3>
    <p>暗号通信やメディア処理機能の品質を保つため、 </p>
<p>pytestを用いたユニットテストと統合テストを導入予定です。</p>
  </li>

  <br>
  
  <li>
    <h3>ユニットテストの対象予定のモジュール</h3>
    <p><strong>RSAKeyExchange</strong>：鍵生成、復号、例外処理の確認 </p>
    <p><strong>AESCipherCFB</strong>：暗号化・復号の正当性（往復で一致）</p>
    <p><strong>MediaProcessor</strong>：ファイル保存、変換パスの返却、例外処理の確認 </p>
  </li>

<br>

  <li>
    <h3>統合テストの例</h3>
    <p>ファイル送信 → ffmpeg変換 → ファイル受信まで</p>
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
    本プロジェクトの全コード・構成・図・UIなどの著作権は、制作者である Tenshin Noji に帰属します。<br><br>
    採用選考や個人的な学習を目的とした閲覧・参照は歓迎しますが、<br><br>
    無断転載・複製・商用利用・二次配布は禁止とさせていただきます。<br><br>
    ライセンス全文はリポジトリ内の <a href="./LICENSE.md" target="_blank">LICENSEファイル</a>をご覧ください。
  </li>
</ul>

<br>
