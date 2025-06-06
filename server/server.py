import socket
import os
import json
from pathlib import Path

import ffmpeg
from Crypto.PublicKey import RSA
from Crypto.Cipher    import AES, PKCS1_OAEP


class RSAKeyExchange:
    
    # RSA鍵ペアを生成（2048ビット）
    def __init__(self):
        self.private_key = RSA.generate(2048)

    # 公開鍵をバイト列として返す（送信用）
    def public_key_bytes(self):
        return self.private_key.publickey().export_key()

    def decrypt_symmetric_key(self, encrypted):
        # クライアントから受信した AES 鍵＋IV を復号
        decrypted_bytes = PKCS1_OAEP.new(self.private_key).decrypt(encrypted)

        # 復号結果から AES 鍵と IV を分離して返す（それぞれ 16 バイト）
        aes_key = decrypted_bytes[:16]
        iv      = decrypted_bytes[16:32]
        return aes_key, iv


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


class SecureSocket:
    
    # ソケット本体と暗号化用の対称暗号オブジェクトを保存
    def __init__(self, sock, cipher):
        self.sock   = sock
        self.cipher = cipher

    # 指定されたバイト数を受信するまで繰り返す
    def recv_exact(self, n):
        buffer = bytearray()
        while len(buffer) < n:
            chunk = self.sock.recv(n - len(buffer))
            if not chunk:
                break
            buffer.extend(chunk)
        return bytes(buffer)

    # 平文を暗号化し、長さ（4バイト）付きで送信
    def sendall(self, plaintext):
        encrypted = self.cipher.encrypt(plaintext)
        self.sock.sendall(len(encrypted).to_bytes(4, 'big') + encrypted)

    def recv(self):
        # 最初の4バイトで受信データの長さを取得
        length_bytes = self.recv_exact(4)
        # 指定バイト数のデータを受信し、復号して返す
        encrypted_data = self.recv_exact(int.from_bytes(length_bytes, 'big'))
        return self.cipher.decrypt(encrypted_data)


class MediaProcessor:
    
    # メディアファイル保存用ディレクトリを作成
    def __init__(self, dpath='processed'):
        self.dpath = dpath
        os.makedirs(self.dpath, exist_ok=True)

    # クライアントからファイルを受信し、保存
    def save_file(self, connection, file_path, file_size):
        with open(file_path, 'wb+') as f:
            while file_size > 0:
                chunk = connection.recv()
                if not chunk:
                    break
                f.write(chunk)
                file_size -= len(chunk)

    # 動画ファイルを指定ビットレートで圧縮
    def compress_video(self, input_file_path, file_name, bitrate='1M'):
        output_file_path = os.path.join(self.dpath, f'compressed_{file_name}')
        ffmpeg.input(input_file_path).output(output_file_path, b=bitrate).overwrite_output().run()
        os.remove(input_file_path)
        return output_file_path

    # 指定された解像度に動画サイズを変更（アスペクト比は維持）
    def change_resolution(self, input_file_path, file_name, resolution):
        width, _ = map(int, resolution.split(':'))
        vf = f"scale={width}:-2"
        output_file_path = os.path.join(self.dpath, f'changed_resolution_{file_name}')
        ffmpeg.input(input_file_path).output(output_file_path, vf=vf).overwrite_output().run()
        os.remove(input_file_path)
        return output_file_path

    # 動画の表示アスペクト比 (Display Aspect Ratio) を変更
    def change_aspect_ratio(self, input_file_path, file_name, aspect_ratio):
        output_file_path = os.path.join(self.dpath, f'changed_aspect_ratio_{file_name}')
        ffmpeg.input(input_file_path).output(output_file_path, vf=f"setdar={aspect_ratio}").overwrite_output().run()
        os.remove(input_file_path)
        return output_file_path

    # 動画ファイルから音声を抽出してMP3に変換
    def convert_to_audio(self, input_file_path, file_name):
        output_file_path = os.path.join(self.dpath, f'converted_to_audio_{Path(file_name).stem}.mp3')
        ffmpeg.input(input_file_path).output(output_file_path, acodec='mp3').overwrite_output().run()
        os.remove(input_file_path)
        return output_file_path

    # 指定範囲の映像をGIFとして切り出し・保存
    def create_gif(self, input_file_path, file_name, start_time, duration, fps=10):
        output_file_path = os.path.join(self.dpath, f'created_gif_{Path(file_name).stem}.gif')
        input_stream = ffmpeg.input(input_file_path, ss=start_time, t=duration)
        ffmpeg.output(input_stream, output_file_path, vf=f'fps={fps},scale=320:-1:flags=lanczos', loop=0).overwrite_output().run()
        os.remove(input_file_path)
        return output_file_path


class TCPServer:
    
    def __init__(self, server_address, server_port, processor):
        self.server_address = server_address
        self.server_port    = server_port
        self.sock           = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((server_address, server_port))
        self.sock.listen()
        
        self.processor      = processor
        self.chunk_size     = 1400

    def start_server(self):
        while True:
            connection, _ = self.sock.accept()
            self.handle_client(connection)

    def handle_client(self, connection):
        secure_conn = None  # 追加：例外時に参照できるよう初期化
        try:
            # 鍵交換を実行（RSA公開鍵交換 → AES鍵受信）
            secure_conn = self.perform_key_exchange(connection)

            # クライアントからリクエスト（ヘッダー＋ボディ）を受信・解析
            request   = self.parse_request(secure_conn)
            json_file = request['json_file']

            # 受信したファイルを保存（チャンク単位で受信）
            input_file_path = os.path.join(self.processor.dpath, json_file['file_name'])
            self.processor.save_file(secure_conn, input_file_path, request['file_size'])

            # ファイル受信完了のACKを送信
            secure_conn.sendall(bytes([0x00]))

            # 指定された操作を実行（圧縮・変換など）
            output_file_path = self.operation_dispatcher(json_file, input_file_path)

            # 処理結果ファイルをクライアントに送信
            self.send_file(secure_conn, output_file_path)

        except Exception as e:
            # エラー時も可能であれば暗号化チャネルで応答
            self.send_error_response(secure_conn if secure_conn else connection, str(e))
        finally:
            # 接続をクローズ
            connection.close()

    def perform_key_exchange(self, conn):
        # RSA 鍵ペアを生成
        key_manager = RSAKeyExchange()

        # 自身の公開鍵をクライアントに送信（長さ 2 バイト + 本体）
        public_key_bytes = key_manager.public_key_bytes()
        conn.sendall(len(public_key_bytes).to_bytes(2, 'big') + public_key_bytes)

        # クライアントから暗号化された AES 鍵＋IV を受信
        encrypted_key_size = int.from_bytes(self.recvn(conn, 2), 'big')
        encrypted_key_iv   = self.recvn(conn, encrypted_key_size)

        # 秘密鍵で復号して AES 鍵と IV を取得
        aes_key, aes_iv    = key_manager.decrypt_symmetric_key(encrypted_key_iv)

        # AES 暗号オブジェクトを作成し、暗号化ソケットでラップ
        symmetric_cipher   = AESCipherCFB(aes_key, aes_iv)
        secure_socket      = SecureSocket(conn, symmetric_cipher)

        return secure_socket

    # 指定されたバイト数を受信するまで繰り返す
    @staticmethod
    def recvn(conn, n):
        buf = bytearray()
        while len(buf) < n:
            chunk = conn.recv(n - len(buf))
            if not chunk:
                break
            buf.extend(chunk)
        return bytes(buf)

    def parse_request(self, connection):
        packet = connection.recv()          # 復号済みパケット全体
        header = packet[:8]                 # 先頭 8 バイト = ヘッダー
        body   = packet[8:]                 # 残り = JSON + メディアタイプ

        # ヘッダーから各フィールドを抽出
        json_size       = int.from_bytes(header[0:2], 'big')
        media_type_size = int.from_bytes(header[2:3], 'big')
        file_size       = int.from_bytes(header[3:8], 'big')

        # ボディからJSONとメディアタイプを抽出
        json_part  = body[:json_size]
        media_part = body[json_size:]

        json_file  = json.loads(json_part.decode('utf-8'))
        media_type = media_part.decode('utf-8')

        # 結果を辞書形式で返す
        return {
            'json_size'         : json_size,
            'media_type_size'   : media_type_size,
            'file_size'         : file_size,
            'json_file'         : json_file,
            'media_type'        : media_type
        }

    def operation_dispatcher(self, json_file, input_file_path):
        # 操作コードとファイル名を取得
        operation = json_file['operation']
        file_name = json_file['file_name']

        if operation == 1:
            return self.processor.compress_video(input_file_path, file_name)

        elif operation == 2:
            resolution = json_file.get('resolution')
            return self.processor.change_resolution(input_file_path, file_name, resolution)

        elif operation == 3:
            aspect_ratio = json_file.get('aspect_ratio')
            return self.processor.change_aspect_ratio(input_file_path, file_name, aspect_ratio)

        elif operation == 4:
            return self.processor.convert_to_audio(input_file_path, file_name)

        elif operation == 5:
            start_time = json_file.get('start_time')
            duration   = json_file.get('duration')
            return self.processor.create_gif(input_file_path, file_name, start_time, duration)

        else:
            raise ValueError(f"Invalid operation code: {operation}")

    def send_file(self, connection, output_file_path):
        # パス処理とメタ情報の準備
        path = Path(output_file_path)
        file_name, media_type = path.name, path.suffix.encode('utf-8')

        # レスポンス用の情報を辞書として作成
        json_data = {
            'file_name': file_name,
            'error': False,
            'error_message': None
        }
        json_bytes = json.dumps(json_data).encode('utf-8')

        # ファイル読み込みと送信
        with open(output_file_path, 'rb') as file:
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)

            packet = self.build_packet(json_bytes, media_type, file_size)
            connection.sendall(packet)

            while chunk := file.read(self.chunk_size):
                connection.sendall(chunk)

    @staticmethod
    def build_packet(json_bytes, media_type_bytes, file_size):
        json_size       = len(json_bytes)
        media_type_size = len(media_type_bytes)
        
        header = (
            json_size.to_bytes(2, 'big') +
            media_type_size.to_bytes(1, 'big') +
            file_size.to_bytes(5, 'big')
        )
        
        return header + json_bytes + media_type_bytes

    def send_error_response(self, connection, error_message):
        # クライアントへ送信するエラー情報を辞書で作成（error=True・エラーメッセージ）
        error_response = {
            'error'         : True,
            'error_message' : error_message
        }
        # 辞書を JSON にシリアライズし、バイト列としてエンコード
        json_bytes = json.dumps(error_response).encode('utf-8')
        # エラー時はメディアタイプを空（b''）、ファイルサイズを 0 にしてパケットを生成
        packet = self.build_packet(json_bytes, b'', 0)
        # connection が SecureSocket なら暗号化されて送信される
        connection.sendall(packet)



if __name__ == "__main__":
    
    # サーバーの IPアドレスと ポート番号 を設定
    server_address = '0.0.0.0'
    server_port    = 9001

    # メディア処理オブジェクトを作成
    processor = MediaProcessor()

    # サーバを起動
    tcp_server = TCPServer(server_address, server_port, processor)
    tcp_server.start_server()
