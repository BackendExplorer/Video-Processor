# server.py

import socket
import os
import json
import logging
from pathlib import Path
import ffmpeg
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Random import get_random_bytes

logging.basicConfig(level=logging.INFO, format='%(message)s')

# ──── 暗号化ユーティリティ ─────────────────────────────

class Encryption:
    def __init__(self):
        # RSA鍵ペアを生成
        self.private_key = RSA.generate(2048)
        self.public_key = self.private_key.publickey()
        self.peer_public_key = None
        self.aes_key = None
        self.iv = None

    def get_public_key_bytes(self):
        return self.public_key.export_key()

    def load_peer_public_key(self, data: bytes):
        self.peer_public_key = RSA.import_key(data)

    def decrypt_symmetric_key(self, encrypted: bytes):
        # クライアントから送られたAES鍵＋IVを復号
        cipher = PKCS1_OAEP.new(self.private_key)
        sym = cipher.decrypt(encrypted)
        self.aes_key = sym[:16]
        self.iv      = sym[16:32]

    def wrap_socket(self, sock: socket.socket):
        # AES-CFB で送受信用ストリーム暗号化ソケットを生成
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
        # client.upload_and_process で send() を呼んでいる部分対応
        self.sendall(data)

    def recv(self) -> bytes:
        # 4バイト長→暗号文→復号
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

# ──── メディア処理ユーティリティ ────────────────────────

class MediaProcessor:
    def __init__(self, dpath='processed'):
        self.dpath = dpath
        os.makedirs(self.dpath, exist_ok=True)
        logging.info("\n=============================================")
        logging.info(f"\n📂 メディア保管用ディレクトリを作成: {self.dpath}")

    def save_file(self, connection, file_path, file_size, chunk_size=1400):
        logging.info(f"📥 ファイル受信開始: {file_path}")
        with open(file_path, 'wb+') as f:
            self.receive_in_chunks(connection, f, file_size, chunk_size)
        logging.info(f"✅ ファイル受信終了: {file_path}")

    def receive_in_chunks(self, connection, file_obj, remaining_size, chunk_size=1400):
        while remaining_size > 0:
            data = connection.recv()
            if not data:
                break
            file_obj.write(data)
            remaining_size -= len(data)

    def compress_video(self, input_file_path, file_name, bitrate='1M'):
        logging.info("\n---------------------------------------------")
        logging.info(f"\n🔧 加工開始: {file_name} - 加工ビットレート: {bitrate}")
        output_file_path = os.path.join(self.dpath, f'compressed_{file_name}')
        ffmpeg.input(input_file_path).output(output_file_path, b=bitrate).run()
        os.remove(input_file_path)
        logging.info("\n✅ 加工完了: " + output_file_path)
        return output_file_path

    def change_resolution(self, input_file_path, file_name, resolution):
        logging.info("\n---------------------------------------------")
        logging.info(f"\n🔧 加工開始: {file_name} - 新解像度: {resolution}")
        output_file_path = os.path.join(self.dpath, f'changed_resolution_{file_name}')
        ffmpeg.input(input_file_path).output(output_file_path, vf=f"scale={resolution}").run()
        os.remove(input_file_path)
        logging.info("\n✅ 解像度変更完了: " + output_file_path)
        return output_file_path

    def change_aspect_ratio(self, input_file_path, file_name, aspect_ratio):
        logging.info(f"\n🔧 加工開始: {file_name} - 新アスペクト比: {aspect_ratio}")
        output_file_path = os.path.join(self.dpath, f'changed_aspect_ratio_{file_name}')
        ffmpeg.input(input_file_path).output(output_file_path, vf=f"setdar={aspect_ratio}").run()
        os.remove(input_file_path)
        logging.info(f"\n✅ アスペクト比変更完了: {output_file_path}")
        return output_file_path

    def convert_to_audio(self, input_file_path, file_name):
        logging.info(f"\n🔧 加工開始: {file_name} - 音声に変換")
        output_file_path = os.path.join(self.dpath, f'converted_to_audio_{Path(file_name).stem}.mp3')
        ffmpeg.input(input_file_path).output(output_file_path, acodec='mp3').run()
        os.remove(input_file_path)
        logging.info(f"\n✅ 音声変換完了: {output_file_path}")
        return output_file_path

    def create_gif(self, input_file_path, file_name, start_time, duration, fps=10):
        logging.info("\n---------------------------------------------")
        logging.info(f"🔧 加工開始: {file_name} - GIF作成 ({start_time}s から {duration}s, {fps}fps)")
        output_file_path = os.path.join(self.dpath, f'created_gif_{Path(file_name).stem}.gif')
        ffmpeg.input(input_file_path).output(
            output_file_path,
            ss=start_time, t=duration,
            vf=f"fps={fps}", pix_fmt='rgb24'
        ).run()
        os.remove(input_file_path)
        logging.info(f"✅ GIF作成完了: {output_file_path}")
        return output_file_path

# ──── TCPサーバー ────────────────────────────────────

class TCPServer:
    def __init__(self, server_address, server_port, processor: MediaProcessor):
        self.server_address = server_address
        self.server_port = server_port
        self.processor = processor
        self.chunk_size = 1400

        # 暗号化インスタンス
        self.encryption = Encryption()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((server_address, server_port))
        self.sock.listen()
        logging.info(f"🚀 サーバーが起動 : {server_address}:{server_port}")

    def start_server(self):
        while True:
            conn, addr = self.accept_connection()
            self.handle_client(conn)

    def accept_connection(self):
        conn, client_address = self.sock.accept()
        logging.info("\n=============================================")
        logging.info(f"\n🔗 新しい接続を確立: {client_address}")
        return conn, client_address

    def handle_client(self, connection):
        try:
            # ── ハンドシェイク ───────────────────────────
            # 1) クライアント公開鍵受信
            raw = connection.recv(2)
            pk_len = int.from_bytes(raw, 'big')
            client_pk = connection.recv(pk_len)
            self.encryption.load_peer_public_key(client_pk)
            logging.info("🔑 クライアント公開鍵受信完了")

            # 2) サーバ公開鍵送信
            server_pk = self.encryption.get_public_key_bytes()
            connection.sendall(len(server_pk).to_bytes(2, 'big') + server_pk)
            logging.info("🔑 サーバ公開鍵送信完了")

            # 3) 対称鍵受信
            raw = connection.recv(2)
            enc_len = int.from_bytes(raw, 'big')
            enc_sym = connection.recv(enc_len)
            self.encryption.decrypt_symmetric_key(enc_sym)
            logging.info("🔒 対称鍵の共有完了")

            # 4) 通信ソケットを暗号化ラップ
            secure_conn = self.encryption.wrap_socket(connection)

            # ── 既存の処理 ─────────────────────────────
            header = self.parse_header(secure_conn)
            json_file, media_type = self.parse_body(
                secure_conn,
                header['json_length'], header['media_type_length']
            )
            input_file_path = os.path.join(self.processor.dpath, json_file['file_name'])
            self.processor.save_file(secure_conn, input_file_path,
                                     header['file_size'], self.chunk_size)

            # ACK
            secure_conn.sendall(bytes([0x00]))

            output_file_path = self.operation_dispatcher(json_file, input_file_path)
            self.send_file(secure_conn, output_file_path)

        except Exception as e:
            logging.error(f"❌ エラー発生: {e}")
            self.send_error_response(connection, str(e))

        finally:
            logging.info("🔚 接続を終了します\n")
            connection.close()

    def parse_header(self, connection):
        data = connection.recv()
        return {
            'json_length': int.from_bytes(data[0:2], 'big'),
            'media_type_length': int.from_bytes(data[2:3], 'big'),
            'file_size': int.from_bytes(data[3:8], 'big')
        }

    def parse_body(self, connection, json_length, media_type_length):
        data = connection.recv()
        json_file = json.loads(data[:json_length].decode('utf-8'))
        media_type = data[json_length:].decode('utf-8')
        return json_file, media_type

    def operation_dispatcher(self, json_file, input_file_path):
        op = json_file['operation']
        fn = {
            1: self.processor.compress_video,
            2: lambda p,n: self.processor.change_resolution(p,n,json_file['resolution']),
            3: lambda p,n: self.processor.change_aspect_ratio(p,n,json_file['aspect_ratio']),
            4: self.processor.convert_to_audio,
            5: lambda p,n: self.processor.create_gif(p,n,json_file['start_time'], json_file['duration']),
        }.get(op)
        if not fn:
            raise ValueError('Invalid operation')
        return fn(input_file_path, json_file['file_name'])

    def send_file(self, connection, output_file_path):
        media_type = Path(output_file_path).suffix.encode('utf-8')
        mt_len = len(media_type)
        with open(output_file_path, 'rb') as f:
            f.seek(0, os.SEEK_END)
            fs = f.tell()
            f.seek(0)
            header = (
                len(json.dumps({'file_name': Path(f.name).name, 'error': False, 'error_message': None}).encode()) .to_bytes(2,'big')
                + mt_len.to_bytes(1,'big')
                + fs.to_bytes(5,'big')
            )
            connection.sendall(header)
            connection.sendall(json.dumps({'file_name': Path(f.name).name, 'error': False, 'error_message': None}).encode() + media_type)

            logging.info("📤 ファイル送信開始")
            while True:
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break
                connection.sendall(chunk)
            logging.info("✅ ファイル送信完了")

    def send_error_response(self, connection, error_message):
        jb = json.dumps({'error': True, 'error_message': error_message}).encode()
        header = len(jb).to_bytes(2,'big') + (0).to_bytes(1,'big') + (0).to_bytes(5,'big')
        connection.sendall(header + jb)


if __name__ == "__main__":
    server_address = '0.0.0.0'
    server_port = 9001
    processor = MediaProcessor()
    server = TCPServer(server_address, server_port, processor)
    server.start_server()
