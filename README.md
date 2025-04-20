# 🎥 Video-Processor ✨
**TCP通信と独自プロトコル（MMP）で動画ファイルを処理するサービス**

## 🖥 デモ
**以下は動画のアスペクト比変更のデモです**

https://github.com/user-attachments/assets/be339ad0-1a5b-4105-a610-feef6faf65c7

**以下の動画では、上側に変換前、下側に変換後を同時に表示しています**

https://github.com/user-attachments/assets/2354d4d1-6439-47c5-88cc-d1e4aeb124a5


## **📎 概要**
- [説明](#説明)
- [セットアップ](#セットアップ)
- [使い方](#使い方)


## **🛠 技術関連**
- [使用技術](#使用技術)
- [クラス図](#クラス図)
- [処理の流れ](#処理の流れ)


## **📍開発のポイント**
- [こだわりのポイント](#こだわりのポイント)
- [苦労した点](#苦労した点)
- [さらに追加したい機能](#さらに追加したい機能)


## **📄 参考情報・ライセンス**
- [参考文献](#参考文献)
- [ライセンス](#ライセンス)

---

## <a id="説明"></a> 📝 説明

**Python**と**TCPソケット通信**を用いた、**メディアファイルの加工・送受信システム**です。<br>
クライアントから指示を送るだけで、サーバーがffmpegを使って自動加工・即返却します。<br>
大容量ファイルのスムーズな送受信と、強力なエラーハンドリングに対応しています。

### できること

- **動画圧縮**  
  指定ビットレートでサイズを軽量化

- **解像度変更**  
  フルHD、HD、SDなどに変換

- **アスペクト比変更**  
  16:9、4:3、1:1などに調整

- **音声抽出**  
  動画から音声ファイルだけを取り出して保存

- **GIF作成**  
  動画の好きな部分を切り取り、GIFアニメーションを作成

### 作成動機

Web開発だけでは触れられない、ファイル処理とTCP通信を実践的に学ぶために開発しました。<br>
メディア加工とネットワーク設計の力を同時に鍛えることを目指しています。





---

## <a id="セットアップ"></a> 🚀 セットアップ

### 1. 前提条件

- **Python 3.8以上**  
  [Python公式サイト](https://www.python.org/downloads/) からインストールできます。

- **Git**  
  [Git公式サイト](https://git-scm.com/) からインストールできます。

- **ffmpeg**  
  [ffmpeg公式サイト](https://ffmpeg.org/download.html) からインストールできます


### 2. リポジトリのクローン

以下のコマンドを使って、このプロジェクトのコードをローカルに取得します：

```bash
git clone https://github.com/BackendExplorer/Video-Processor.git
```
```bash
cd Video-Processor
```

---

## <a id="使い方"></a>▶️ 使い方

### 1. サーバ起動

サーバスクリプトを実行し、クライアントからのファイルアップロードと加工リクエストを待機します。

```bash
python3 server.py
```
サーバは接続された複数のクライアントとのやりとりを同時に処理します。

### 2. クライアント起動
別のターミナルを開き、以下のコマンドでクライアントを起動します。

```bash
python3 client.py
```
クライアントを複数起動すれば、同時に複数ファイルのアップロード・加工依頼をテストすることができます。


### 3. 操作手順
以下は、このアプリの基本的な操作手順です

```mermaid
flowchart TD
    Start(["クライアント起動"])
    アップロード["・ファイル選択<br>・アップロード"]
    加工["ファイル加工"]
    通知["加工完了通知"]
    ダウンロード["・ファイルダウンロード<br>・保存"]
    完了(["完了"])
    エラー(["エラー発生"])

    Start --> アップロード
    アップロード -- 成功 --> 加工
    アップロード -- 失敗 --> エラー
    加工 --> 通知 --> ダウンロード
    ダウンロード -- 成功 --> 完了
    ダウンロード -- 失敗 --> エラー
```



---


## <a id="使用技術"></a>🛠 使用技術

| カテゴリ       | 技術スタック                                                                 |
|----------------|------------------------------------------------------------------------------|
| 開発言語       | Python 3.8以上<br>（標準ライブラリ使用：`socket`, `os`, `json`, `logging`, `pathlib`, `sys`, `re`） |
| 通信技術       | TCPソケット通信によるファイル送受信<br>カスタムヘッダー設計によるメタデータ管理 |
| メディア加工   | `ffmpeg` ライブラリをPythonから呼び出して動画・音声処理 |
| 開発環境       | macOS  ・ VSCode                               |
| バージョン管理 | Git（バージョン管理）・GitHub（コード共有・公開）                          |
| 描画ツール     | Mermaid （必要に応じてシーケンス図など作成） |

### 技術選定の理由

- **Python**  
  シンプルな構文と豊富な標準ライブラリにより、ネットワーク通信やファイル処理を素早く実装可能なため採用しました。

- **socket通信（TCP）**  
  ファイルアップロード・ダウンロードにおいて、データの信頼性と順序保証が必須であったため、TCP通信を採用しました。

- **ffmpegライブラリ**  
  高性能かつ多機能なメディア加工エンジンであり、Pythonから簡単に呼び出し可能なため選定しました。  
  これにより、動画圧縮・解像度変更・音声抽出・GIF作成といった多様なニーズに柔軟に対応できます。

- **標準ライブラリ（os, json, pathlib, logging, sys, re）**  
  追加ライブラリ不要で、システム制御、ファイル管理、エラーハンドリング、データ構造化が完結できるため選択しました。


---


## <a id="クラス図"></a>📦 クラス図と構成

### <a id="server.py のクラス図"></a> server.py のクラス図

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

 [サーバプログラムを見る](https://github.com/BackendExplorer/Video-Processor/blob/main/server.py)



### <a id="client.py のクラス図"></a> client.py のクラス図


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

[クライアントプログラムを見る](https://github.com/BackendExplorer/Video-Processor/blob/main/client.py)


### <a id="server.py のクラス図"></a> 


## <a id="処理の流れ"></a>🔀処理の流れ

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

<img width="791" alt="スクリーンショット 2025-04-20 20 29 19" src="https://github.com/user-attachments/assets/fec958f6-9d2e-4c68-a4f0-ee4f4d08a0b3" />



---
## <a id="こだわりのポイント"></a> ✨ こだわりのポイント

この図は、動画転送のために設計された独自プロトコル MMP (Multiple Media Protocol)　のパケット構造を表します



<img width="790" alt="スクリーンショット 2025-04-20 20 28 14" src="https://github.com/user-attachments/assets/e3d90ebf-6210-40a5-8442-4c301867c7c1" />





---
## <a id="苦労した点"></a> ⚠️ 苦労した点


---

## <a id="さらに追加したい機能"></a> 🌱 さらに追加したい機能


---
## <a id="参考文献"></a>📄 参考文献


### 公式ドキュメント


### 参考にしたサイト



## <a id="ライセンス"></a>👤 ライセンス
このプロジェクトは [MIT License](https://opensource.org/licenses/MIT) のもとで公開されています。  
自由に利用、改変、再配布が可能ですが、利用の際は本ライセンス表記を保持してください。
