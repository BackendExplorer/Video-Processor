import socket
import os
import json
from pathlib import Path
import ffmpeg


# メディアファイルの保存・加工を担当するクラス
class MediaProcessor:

    def __init__(self, dpath='processed'):
        self.dpath = dpath
        os.makedirs(self.dpath, exist_ok=True)

    # クライアントから送信されたファイルを保存する関数
    def save_file(self, connection, file_path, file_size, chunk_size=1400):
        with open(file_path, 'wb+') as f:
            self.receive_in_chunks(connection, f, file_size, chunk_size)

    # チャンク単位でデータを受信してファイルに書き込む関数
    def receive_in_chunks(self, connection, file_obj, remaining_size, chunk_size=1400):
        while remaining_size > 0:
            data = connection.recv(min(remaining_size, chunk_size))
            if not data:
                break
            file_obj.write(data)
            remaining_size -= len(data)

    # 動画を指定ビットレートで圧縮する関数
    def compress_video(self, input_file_path, file_name, bitrate='1M'):
        output_file_path = os.path.join(self.dpath, f'compressed_{file_name}')
        self._run_ffmpeg(input_file_path, output_file_path, b=bitrate)
        return output_file_path

    # 動画の解像度を変更する関数
    def change_resolution(self, input_file_path, file_name, resolution):
        output_file_path = os.path.join(self.dpath, f'changed_resolution_{file_name}')
        self._run_ffmpeg(input_file_path, output_file_path, vf=f"scale={resolution}")
        return output_file_path

    # 動画のアスペクト比を変更する関数
    def change_aspect_ratio(self, input_file_path, file_name, aspect_ratio):
        output_file_path = os.path.join(self.dpath, f'changed_aspect_ratio_{file_name}')
        self._run_ffmpeg(input_file_path, output_file_path, vf=f"setdar={aspect_ratio}")
        return output_file_path

    # 動画を音声ファイル（mp3）に変換する関数
    def convert_to_audio(self, input_file_path, file_name):
        output_file_path = os.path.join(self.dpath, f'converted_to_audio_{Path(file_name).stem}.mp3')
        self._run_ffmpeg(input_file_path, output_file_path, acodec='mp3')
        return output_file_path

    # 動画から指定範囲をGIFとして切り出す関数
    def create_gif(self, input_file_path, file_name, start_time, duration, fps=10):
        output_file_path = os.path.join(self.dpath, f'created_gif_{Path(file_name).stem}.gif')
        self._run_ffmpeg(input_file_path, output_file_path, ss=start_time, t=duration, vf=f"fps={fps}", pix_fmt='rgb24')
        return output_file_path

    # ffmpegコマンドを実行する内部関数
    def _run_ffmpeg(self, input_path, output_path, **kwargs):
        if os.path.exists(output_path):
            os.remove(output_path)
        ffmpeg.input(input_path).output(output_path, **kwargs).run()
        os.remove(input_path)


# TCP通信でファイルの送受信と加工指示を受け付けるサーバークラス
class TCPServer:

    def __init__(self, server_address, server_port, processor: MediaProcessor):
        self.server_address = server_address
        self.server_port = server_port
        self.processor = processor
        self.chunk_size = 1400

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((server_address, server_port))
        self.sock.listen()
        print(f'Starting server on {server_address}:{server_port}')

    # サーバーを起動して接続を待機する関数
    def start_server(self):
        while True:
            connection, client_address = self.accept_connection()
            self.handle_client(connection)

    # クライアントからの接続を受け入れる関数
    def accept_connection(self):
        connection, client_address = self.sock.accept()
        print(f'Connection from {client_address}')
        return connection, client_address

    # クライアントとのセッションを処理する関数
    def handle_client(self, connection):
        try:
            header = self.parse_header(connection)
            json_file, media_type = self.parse_body(connection, header['json_length'], header['media_type_length'])

            input_file_path = os.path.join(self.processor.dpath, json_file['file_name'])
            self.processor.save_file(connection, input_file_path, header['file_size'], self.chunk_size)

            connection.sendall(bytes([0x00]))  # 成功レスポンス送信

            output_file_path = self.operation_dispatcher(json_file, input_file_path)
            self.send_file(connection, output_file_path)

        except Exception as e:
            print(f'Error: {e}')
            self.send_error_response(connection, str(e))

        finally:
            print("Closing connection")
            connection.close()

    # ヘッダーを受信して解析する関数
    def parse_header(self, connection):
        header = connection.recv(8)
        return {
            'json_length': int.from_bytes(header[0:2], 'big'),
            'media_type_length': int.from_bytes(header[2:3], 'big'),
            'file_size': int.from_bytes(header[3:8], 'big')
        }

    # ボディを受信して解析する関数
    def parse_body(self, connection, json_length, media_type_length):
        body = connection.recv(json_length + media_type_length)
        json_file = json.loads(body[:json_length].decode('utf-8'))
        media_type = body[json_length:].decode('utf-8')
        return json_file, media_type

    # リクエストに応じたメディア加工を行う関数
    def operation_dispatcher(self, json_file, input_file_path):
        file_name = json_file['file_name']
        operation = json_file['operation']

        if operation == 1:
            return self.processor.compress_video(input_file_path, file_name)
        elif operation == 2:
            return self.processor.change_resolution(input_file_path, file_name, json_file['resolution'])
        elif operation == 3:
            return self.processor.change_aspect_ratio(input_file_path, file_name, json_file['aspect_ratio'])
        elif operation == 4:
            return self.processor.convert_to_audio(input_file_path, file_name)
        elif operation == 5:
            return self.processor.create_gif(input_file_path, file_name, json_file['start_time'], json_file['duration'])
        else:
            raise ValueError('Invalid operation')

    # 加工結果ファイルをクライアントへ送信する関数
    def send_file(self, connection, output_file_path):
        media_type = Path(output_file_path).suffix
        media_type_bytes = media_type.encode('utf-8')
        media_type_length = len(media_type_bytes)

        with open(output_file_path, 'rb') as f:
            file_size = f.seek(0, os.SEEK_END)
            f.seek(0)

            file_name = Path(f.name).name
            json_file = {'file_name': file_name, 'error': False, 'error_message': None}
            json_bytes = json.dumps(json_file).encode('utf-8')

            self.send_header_and_metadata(connection, json_bytes, media_type_bytes, file_size)

            data = f.read(self.chunk_size)
            while data:
                connection.sendall(data)
                data = f.read(self.chunk_size)

    # ヘッダーとメタデータを送信する関数
    def send_header_and_metadata(self, connection, json_bytes, media_type_bytes, file_size):
        header = self.build_header(len(json_bytes), len(media_type_bytes), file_size)
        connection.sendall(header)
        connection.sendall(json_bytes + media_type_bytes)

    # エラー発生時にクライアントへエラーレスポンスを送信する関数
    def send_error_response(self, connection, error_message):
        json_file = {'error': True, 'error_message': error_message}
        json_bytes = json.dumps(json_file).encode('utf-8')
        header = self.build_header(len(json_bytes), 0, 0)
        connection.sendall(header)
        connection.sendall(json_bytes)

    # カスタムプロトコル用ヘッダーを作成する関数
    def build_header(self, json_length, media_type_length, file_size):
        return json_length.to_bytes(2, 'big') + media_type_length.to_bytes(1, 'big') + file_size.to_bytes(5, 'big')


if __name__ == "__main__":
    server_address = '0.0.0.0'
    server_port = 9001
    processor = MediaProcessor()
    server = TCPServer(server_address, server_port, processor)
    server.start_server()
