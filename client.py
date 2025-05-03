# client.py

import socket
import os
import json
import logging
from pathlib import Path
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Random import get_random_bytes

logging.basicConfig(level=logging.INFO, format='%(message)s')

# ──── 暗号化ユーティリティ ─────────────────────────────

class Encryption:
    def __init__(self):
        self.private_key = RSA.generate(2048)
        self.public_key = self.private_key.publickey()
        self.peer_public_key = None
        self.aes_key = None
        self.iv = None

    def get_public_key_bytes(self):
        return self.public_key.export_key()

    def load_peer_public_key(self, data: bytes):
        self.peer_public_key = RSA.import_key(data)

    def generate_symmetric_key(self):
        # AES鍵＋IV をまとめてバイト列で返す
        self.aes_key = get_random_bytes(16)
        self.iv      = get_random_bytes(16)
        return self.aes_key + self.iv

    def encrypt_symmetric_key(self, sym: bytes):
        cipher = PKCS1_OAEP.new(self.peer_public_key)
        return cipher.encrypt(sym)

    def wrap_socket(self, sock: socket.socket):
        cipher_enc = AES.new(self.aes_key, AES.MODE_CFB, iv=self.iv, segment_size=128)
        cipher_dec = AES.new(self.aes_key, AES.MODE_CFB, iv=self.iv, segment_size=128)
        return EncryptedSocket(sock, cipher_enc, cipher_dec)

class EncryptedSocket:
    def __init__(self, sock: socket.socket, cipher_enc: AES, cipher_dec: AES):
        self.sock = sock
        self.cipher_enc = cipher_enc
        self.cipher_dec = cipher_dec

    def sendall(self, data: bytes):
        ct = self.cipher_enc.encrypt(data)
        length = len(ct).to_bytes(4, 'big')
        self.sock.sendall(length + ct)

    def send(self, data: bytes):
        self.sendall(data)

    def recv(self) -> bytes:
        lb = self._recvn(4)
        if not lb:
            return b''
        length = int.from_bytes(lb, 'big')
        ct = self._recvn(length)
        return self.cipher_dec.decrypt(ct)

    def _recvn(self, n: int) -> bytes:
        data = b''
        while len(data) < n:
            packet = self.sock.recv(n - len(data))
            if not packet:
                break
            data += packet
        return data

    def close(self):
        self.sock.close()

# ──── ファイル受信ユーティリティ ────────────────────────

class FileHandler:
    def __init__(self, dpath='receive'):
        self.dpath = dpath
        os.makedirs(self.dpath, exist_ok=True)

    def save_received_file(self, file_name, connection, file_size, chunk_size=1400):
        output_file_path = os.path.join(self.dpath, file_name)
        with open(output_file_path, 'wb+') as f:
            while file_size > 0:
                data = connection.recv()
                f.write(data)
                file_size -= len(data)
        return output_file_path

# ──── TCPクライアント ──────────────────────────────────

class TCPClient:
    def __init__(self, server_address, server_port, handler: FileHandler):
        self.server_address = server_address
        self.server_port = server_port
        self.handler = handler
        self.chunk_size = 1400
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 暗号化インスタンス
        self.encryption = Encryption()

    def upload_and_process(self, file_path, operation, operation_details={}):
        # 1) サーバ接続
        self.sock.connect((self.server_address, self.server_port))

        # ── ハンドシェイク ───────────────────────────
        # a) クライアント公開鍵送信
        client_pk = self.encryption.get_public_key_bytes()
        self.sock.sendall(len(client_pk).to_bytes(2,'big') + client_pk)
        logging.info("🔑 クライアント公開鍵送信完了")

        # b) サーバ公開鍵受信
        raw = self.sock.recv(2)
        srv_len = int.from_bytes(raw, 'big')
        srv_pk = self.sock.recv(srv_len)
        self.encryption.load_peer_public_key(srv_pk)
        logging.info("🔑 サーバ公開鍵受信完了")

        # c) 対称鍵生成→暗号化→送信
        sym = self.encryption.generate_symmetric_key()
        enc_sym = self.encryption.encrypt_symmetric_key(sym)
        self.sock.sendall(len(enc_sym).to_bytes(2,'big') + enc_sym)
        logging.info("🔒 対称鍵共有完了")

        # d) 暗号化ソケットにラップ
        secure_sock = self.encryption.wrap_socket(self.sock)
        # 以後 self.sock を secure_sock に置き換え
        self.sock = secure_sock

        # ── 既存の送受信処理 ───────────────────────
        _, media_type = os.path.splitext(file_path)
        media_bytes = media_type.encode('utf-8')

        with open(file_path, 'rb') as f:
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
            f.seek(0)

            payload = {'file_name': os.path.basename(f.name), 'operation': operation}
            payload.update(operation_details)
            json_bytes = json.dumps(payload).encode('utf-8')

            # ヘッダー送信
            header = (
                len(json_bytes).to_bytes(2, 'big')
                + len(media_bytes).to_bytes(1, 'big')
                + file_size.to_bytes(5, 'big')
            )
            self.sock.sendall(header)
            self.sock.sendall(json_bytes + media_bytes)

            # ファイルデータ送信
            data = f.read(self.chunk_size)
            while data:
                self.sock.send(data)
                data = f.read(self.chunk_size)

            # ACK 受信
            response = self.sock.recv()
            if response != bytes([0x00]):
                raise Exception("サーバーがエラーを返しました")

        # レスポンスファイル受信
        return self.receive_file()

    def receive_file(self):
        # ヘッダー受信
        header = self.sock.recv()
        json_len = int.from_bytes(header[0:2], 'big')
        media_len = int.from_bytes(header[2:3], 'big')
        file_size = int.from_bytes(header[3:8], 'big')

        body = self.sock.recv()
        info = json.loads(body[:json_len].decode('utf-8'))
        if info['error']:
            raise Exception(f"サーバーエラー: {info['error_message']}")

        file_name = info['file_name']
        received = self.handler.save_received_file(
            file_name, self.sock, file_size, self.chunk_size
        )
        self.sock.close()
        return received

if __name__ == "__main__":
    client = TCPClient('127.0.0.1', 9001, FileHandler())
    # 例: 動画圧縮（operation=1）
    out = client.upload_and_process('input.mp4', 1, {})
    logging.info("受信ファイル: " + out)
