# 🎥 Video-Processor ✨
**TCP通信と独自プロトコル（MMP）で動画ファイルを処理するサービス**

## 🖥 デモ
https://github.com/user-attachments/assets/be339ad0-1a5b-4105-a610-feef6faf65c7



https://github.com/user-attachments/assets/2354d4d1-6439-47c5-88cc-d1e4aeb124a5




### 1. 動画の圧縮

| Before | After |
|:------:|:-----:|
| ![圧縮前](<img width="1013" alt="スクリーンショット 2025-04-19 14 58 36" src="https://github.com/user-attachments/assets/01cd5b7c-caa6-4a02-a906-c1a852e882c2" />
) | ![圧縮後]() |

---

### 2. 解像度変更

| Before | After |
|:------:|:-----:|
| ![解像度変更前](リンクをここに) | ![解像度変更後](リンクをここに) |

---

<h3>3. アスペクト比変更 （16:9→1:1)</h3>

<table style="border: 1px solid #ccc; border-collapse: collapse;">
  <tr>
    <td align="center" style="border-right: 1px solid #ccc; border-bottom: 1px solid #ccc; padding: 10px;">
      <b>Before (16:9)</b>
    </td>
    <td align="center" style="border-bottom: 1px solid #ccc; padding: 10px;">
      <b>After (1:1)</b>
    </td>
  </tr>
  <tr>
    <td align="center" style="border-right: 1px solid #ccc; padding: 10px;">
      <img src="https://github.com/user-attachments/assets/00dd03d7-9969-4467-930b-7fa6f30b1ed6" height="300px"><br>
      <a href="動画リンクURL1" target="_blank" style="display: inline-block; margin-top: 8px; padding: 6px 12px; background-color: #007bff; color: #fff; text-decoration: none; border-radius: 4px;">▶︎ 動画を見る</a>
    </td>
    <td align="center" style="padding: 10px;">
      <img src="https://github.com/user-attachments/assets/b8080bde-8512-4f73-b23d-a1623060b03a" height="300px"><br>
      <a href="動画リンクURL2" target="_blank" style="display: inline-block; margin-top: 8px; padding: 6px 12px; background-color: #28a745; color: #fff; text-decoration: none; border-radius: 4px;">▶︎ 動画を見る</a>
    </td>
  </tr>
</table>

---

### 4. 音声変換

| Before（動画） | After（音声ファイル） |
|:--------------:|:--------------------:|
| 🎥 [動画ファイル（リンク）](リンクをここに) | 🔈 [音声ファイル（リンク）](リンクをここに) |

---

### 5. GIF作成  (MP4→GIF )

<table style="border: 1px solid #ccc; border-collapse: collapse;">
  <tr>
    <td align="center" style="border-right: 1px solid #ccc; border-bottom: 1px solid #ccc; padding: 10px;">
      <b>Before (MP4)</b>
    </td>
    <td align="center" style="border-bottom: 1px solid #ccc; padding: 10px;">
      <b>After (GIF)</b>
    </td>
  </tr>
  <tr>
    <td align="center" style="border-right: 1px solid #ccc; padding: 10px;">
      <img src="https://github.com/user-attachments/assets/00dd03d7-9969-4467-930b-7fa6f30b1ed6" height="300px">
    </td>
    <td align="center" style="padding: 10px;">
      <img src="https://github.com/user-attachments/assets/ab86d883-63d9-45e0-93b9-6efa0f2004b8" height="300px">
    </td>
  </tr>
</table>

---



## **📎 概要**
- [説明](#説明)
- [セットアップ](#セットアップ)
- [利用方法](#利用方法)


## **🛠 技術関連**
- [使用技術](#使用技術)
- [クラス図](#クラス図)
- [処理の流れ](#処理の流れ)


## **📍開発のポイント**
- [こだわりのポイント](#こだわりのポイント)
- [苦労した点](#苦労した点)
- [さらに追加したい機能](#さらに追加したい機能)


## **📄 参考情報**
- [参考文献](#参考文献)

---

## <a id="説明"></a> 📎 説明



###  主な特徴


---

## <a id="セットアップ"></a> 🚀 セットアップ

### 1. 前提条件

- **Python 3.8以上**  
  [Python公式サイト](https://www.python.org/downloads/) からインストールできます

- **Git**  
  [Git公式サイト](https://git-scm.com/) からインストールできます



### 2. リポジトリのクローン

以下のコマンドを使って、このプロジェクトのコードをローカルに取得します：

```bash
git clone https://github.com/BackendExplorer/Video-Processor.git
```
```bash
cd Video-Processor
```

---

## <a id="利用方法"></a>▶️ 利用方法


---


## <a id="使用技術"></a>🛠 使用技術
| カテゴリ       | 技術スタック                                                                 |
|----------------|------------------------------------------------------------------------------|
| 開発言語       | Python 3.13.2<br>（標準ライブラリのみ使用：`socket`, `threading`, `secrets`, `logging`, `base64`, `time`, `sys`） |
| 通信技術       | TCP / UDP ソケット通信<br>独自プロトコル「TCRP（Talk Chat Room Protocol）」による通信設計 |
| 並列処理       | `threading` モジュールによるマルチスレッド処理<br>（クライアント・サーバー間の非同期処理を実現） |
| 開発環境       | macOS ・ VSCode                               |
| バージョン管理 | Git（バージョン管理）・GitHub（コード共有・公開）                          |
| 描画ツール | Mermaid ・ Latex |

### 技術選定の理由


---

<div style="font-size:120%; line-height:1.6;">
  
## <a id="処理の流れ"></a>🔀処理の流れ


---

## <a id="クラス図"></a>📦 クラス図と構成


### <a id="server.py のクラス図"></a> 

---
## <a id="こだわりのポイント"></a> ✨ こだわりのポイント

---
## <a id="苦労した点"></a> ⚠️ 苦労した点


---

## <a id="さらに追加したい機能"></a> 🌱 さらに追加したい機能


---
## <a id="参考文献"></a>📄 参考文献

### 公式ドキュメント


### 参考にしたサイト

