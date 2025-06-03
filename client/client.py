import socket
import os
import json
import logging
from pathlib import Path

from Crypto.PublicKey import RSA
from Crypto.Cipher    import AES, PKCS1_OAEP
from Crypto.Random    import get_random_bytes

logging.basicConfig(level=logging.INFO, format='%(message)s')



class AESCipherCFB:
    
     # 対称鍵と初期化ベクトル（IV）を保存
    def __init__(self, key, iv):
        self.key = key
        self.iv  = iv
        
    # AES CFBモードでデータを暗号化して返す
    def encrypt(self, data):
        return AES.new(self.key, AES.MODE_CFB, iv=self.iv, segment_size=128).encrypt(data)

     # AES CFBモードでデータを復号して返す
    def decrypt(self, data):
        return AES.new(self.key, AES.MODE_CFB, iv=self.iv, segment_size=128).decrypt(data)


class Encryption:
    
    def __init__(self):
        # self.private_key = RSA.generate(2048)  # クライアント公開鍵生成は不要
        self.peer_public_key = None
        self.aes_key = self.iv = None

    # 通信相手から受け取った公開鍵をインポート
    def load_peer_public_key(self, data):
        self.peer_public_key = RSA.import_key(data)

    # ランダムなAES鍵とIV（各16バイト）を生成
    def generate_symmetric_key(self):
        self.aes_key = get_random_bytes(16)
        self.iv      = get_random_bytes(16)

        # AES鍵とIVを結合して返す（RSA暗号化用）
        return self.aes_key + self.iv

    # 相手の公開鍵で対称鍵＋IVをRSA暗号化して返す
    def encrypt_symmetric_key(self, sym):
        return PKCS1_OAEP.new(self.peer_public_key).encrypt(sym)

    # 対称鍵でソケット通信を暗号化するSecureSocketを生成
    def wrap_socket(self, sock):        
        cipher = AESCipherCFB(self.aes_key, self.iv)
        return SecureSocket(sock, cipher)



class SecureSocket:

    # ソケット本体と暗号化用の対称暗号オブジェクトを保存
    def __init__(self, sock, cipher):
        self.sock   = sock
        self.cipher = cipher

    # 指定されたバイト数を受信するまで繰り返す
    def recv_exact(self, n):
        buf = bytearray()
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                break
            buf.extend(chunk)
        return bytes(buf)

    # 平文を暗号化し、長さ（4バイト）付きで送信
    def sendall(self, plaintext):
        ciphertext = self.cipher.encrypt(plaintext)
        self.sock.sendall(len(ciphertext).to_bytes(4, 'big') + ciphertext)

    # 暗号化されたデータを受信して復号して返す
    def recv(self):
        length = self.recv_exact(4)
        if not length:
            return b''
        ciphertext = self.recv_exact(int.from_bytes(length, 'big'))
        return self.cipher.decrypt(ciphertext)

    # ソケットを閉じる
    def close(self):
        self.sock.close()

class TCPClient:

    def __init__(self, server_address, server_port, dpath='receive'):
        self.server_address = server_address
        self.server_port    = server_port
        self.chunk_size     = 1400
        
        self.encryption     = Encryption()
        self.dpath = dpath
        os.makedirs(self.dpath, exist_ok=True)

    # 指定されたバイト数を受信するまで繰り返す
    def recv_exact(self, sock, n):
        buf = bytearray()
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                break
            buf.extend(chunk)
        return bytes(buf)

    def perform_key_exchange(self):
        # TCP ソケットを作成して接続
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((self.server_address, self.server_port))

        # サーバの公開鍵を受信してインポート
        pubkey_length = int.from_bytes(self.recv_exact(tcp_socket, 2), 'big')
        server_pubkey = self.recv_exact(tcp_socket, pubkey_length)
        self.encryption.load_peer_public_key(server_pubkey)
        
        logging.info("🔑 サーバ公開鍵受信完了")

        # 対称鍵（AES + IV）を生成し、サーバ公開鍵で暗号化して送信
        sym_key       = self.encryption.generate_symmetric_key()
        encrypted_key = self.encryption.encrypt_symmetric_key(sym_key)
        tcp_socket.sendall(len(encrypted_key).to_bytes(2, 'big') + encrypted_key)
        
        logging.info("🔒 対称鍵共有完了")

        # 暗号化されたソケットでラップ
        self.sock = self.encryption.wrap_socket(tcp_socket)

    def upload_and_process(self, file_path, operation, operation_details={}):
        # 鍵交換と暗号化ソケットの確立
        self.perform_key_exchange()

        # 拡張子（例: .mp4）をメディアタイプとして抽出
        media_type = Path(file_path).suffix.encode('utf-8')
        media_type_size = len(media_type)

        with open(file_path, 'rb') as file:
            # ファイルサイズ取得
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)

            # メタ情報ペイロードを構築（JSON形式）
            payload = {
                'file_name': Path(file.name).name,
                'operation': operation
            }
            
            payload.update(operation_details)
            json_bytes   = json.dumps(payload).encode('utf-8')
            json_size  = len(json_bytes)

            # ヘッダー: JSON長(2B) + メディアタイプ長(1B) + ファイルサイズ(5B)
            header = (
                json_size.to_bytes(2, 'big')       +
                media_type_size.to_bytes(1, 'big') +
                file_size.to_bytes(5, 'big')
            )
            
            # ヘッダー + JSON + メディアタイプを送信
            self.sock.sendall(header)
            self.sock.sendall(json_bytes + media_type)

            # ファイル本体をチャンク送信
            while True:
                chunk = file.read(self.chunk_size)
                if not chunk:
                    break
                self.sock.sendall(chunk)

        # サーバ応答を確認
        if self.sock.recv() != bytes([0x00]):
            raise Exception("サーバーがエラーを返しました")

        return self.receive_file()

    def receive_file(self):
        # ヘッダーとボディをそれぞれ受信
        header = self.sock.recv()
        body   = self.sock.recv()

        # ヘッダーから各フィールドを抽出
        json_size       = int.from_bytes(header[0:2], 'big')
        media_type_size = int.from_bytes(header[2:3], 'big')
        file_size       = int.from_bytes(header[3:8], 'big')

        # ボディから JSON 部とメディアタイプ部に分割
        json_part  = body[:json_size]
        media_part = body[json_size:]

        # JSON デコード
        info = json.loads(json_part.decode('utf-8'))
        if info['error']:
            raise Exception(f"サーバーエラー: {info['error_message']}")

        file_name = info['file_name']

        # ファイルを受信して保存
        out_path = self.save_received_file(file_name, self.sock, file_size, self.chunk_size)
        self.sock.close()
        return out_path

    def save_received_file(self, file_name, connection, file_size, chunk_size=1400):
        # 出力先ファイルパスを構築
        output_path = os.path.join(self.dpath, file_name)

        with open(output_path, 'wb') as file:
            remaining = file_size
            while remaining > 0:
                chunk = connection.recv()
                if not chunk:
                    break
                file.write(chunk)
                remaining -= len(chunk)

        return output_path



if __name__ == "__main__":
    
    # 接続先サーバーの IP アドレスとポート番号
    server_address = '127.0.0.1'
    server_port    = 9001

    # TCP クライアントを初期化してファイルをアップロード・処理
    client = TCPClient(server_address, server_port)
    result = client.upload_and_process('input.mp4', 1, {})

    logging.info("受信ファイル: " + result)
