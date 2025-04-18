import socket
import os
import json
import sys
from pathlib import Path
import ffmpeg
import re         


# ファイル操作（アップロード用ファイル選択・オプション指定・保存）を担当するクラス
class FileHandler:

    def __init__(self, dpath='recieve'):
        self.dpath = dpath
        os.makedirs(self.dpath, exist_ok=True)

    # ファイルパスを入力・検証する関数
    def input_file_path(self):
        valid_extensions = ('.mp4', '.avi')
        while True:
            file_path = input("ファイルパスを入力してください（mp4、aviのいずれかの拡張子）: ")
            if file_path.endswith(valid_extensions):
                print(f"有効なファイルパスが入力されました: {file_path}")
                return file_path
            else:
                print("無効なファイル拡張子です。もう一度試してください。")

    # オペレーション番号を入力・検証する関数
    def input_operation(self):
        while True:
            print("1: 動画の圧縮, 2: 動画の解像度の変更, 3: 動画のアスペクト比の変更, 4: 動画を音声に変換, 5: 指定した時間範囲でGIFの作成")
            try:
                operation = int(input("オペレーションを入力してください(1-5): "))
                if operation in range(1, 6):
                    print(f"選択されたオペレーション: {operation}")
                    return operation
                else:
                    print("無効な選択です。1から5の数字を入力してください。")
            except ValueError:
                print("無効な入力です。数字を入力してください。")

    # 各オペレーションごとに詳細情報を入力する関数
    def input_operation_details(self, operation, json_file, file_path):
        if operation == 2:
            json_file['resolution'] = self.input_resolution()
        elif operation == 3:
            json_file['aspect_ratio'] = self.input_aspect_ratio()
        elif operation == 5:
            start_time, duration = self.input_gif_time_range(file_path)
            json_file['start_time'] = start_time
            json_file['duration'] = duration
        return json_file

    # 解像度の選択を受け付ける関数
    def input_resolution(self):
        resolutions = {"1": "1920:1080", "2": "1280:720", "3": "720:480"}
        while True:
            print("1: フルHD(1920:1080), 2: HD(1280:720), 3: SD(720:480)")
            resolution = input("希望する解像度の番号を入力してください: ")
            if resolution in resolutions:
                return resolutions[resolution]
            else:
                print("無効な選択です。もう一度入力してください。")

    # アスペクト比の選択を受け付ける関数
    def input_aspect_ratio(self):
        aspect_ratios = {"1": "16/9", "2": "4/3", "3": "1/1"}
        while True:
            print("1: (16:9), 2: (4:3), 3: (1:1)")
            aspect_ratio = input("希望するアスペクト比の番号を入力してください: ")
            if aspect_ratio in aspect_ratios:
                return aspect_ratios[aspect_ratio]
            else:
                print("無効な選択です。もう一度入力してください。")

    # GIF作成用の開始時間・再生時間を入力する関数
    def input_gif_time_range(self, file_path):
        video_duration = self.get_video_duration(file_path)
        HH = video_duration // 3600
        MM = (video_duration % 3600) // 60
        SS = video_duration % 60
        while True:
            print(f"動画の長さは{int(HH):02}:{int(MM):02}:{int(SS):02}です。")
            start_time = input("開始時間を入力してください（例: 00:00:10）: ")
            if re.match(r'^\d{2}:\d{2}:\d{2}$', start_time):
                st_HH, st_MM, st_SS = map(int, start_time.split(":"))
                start_time_sec = st_HH * 3600 + st_MM * 60 + st_SS
                if start_time_sec < video_duration:
                    break
                else:
                    print("開始時間は動画の長さより短くしてください。")
            else:
                print("無効な時間形式です。もう一度入力してください。")

        while True:
            duration = input("再生時間を秒単位で入力してください（例: 10）: ")
            if duration.isdigit():
                duration = float(duration)
                if 0 < duration <= (video_duration - start_time_sec):
                    return start_time_sec, duration
                else:
                    print("無効な再生時間です。もう一度入力してください。")
            else:
                print("無効な入力です。数字を入力してください。")

    # 動画ファイルの長さ（秒）を取得する関数
    def get_video_duration(self, file_path):
        probe = ffmpeg.probe(file_path)
        return float(probe['format']['duration'])

    # 受信したファイルを保存する関数
    def save_received_file(self, file_name, connection, file_size, chunk_size=1400):
        output_file_path = os.path.join(self.dpath, file_name)
        with open(output_file_path, 'wb+') as f:
            while file_size > 0:
                data = connection.recv(min(file_size, chunk_size))
                f.write(data)
                file_size -= len(data)
        print("ダウンロードに成功しました: ", output_file_path)


# TCP通信でサーバに接続してファイルを送信・受信するクライアントクラス
class TCPClient:

    def __init__(self, server_address, server_port, handler: FileHandler):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = server_address
        self.server_port = server_port
        self.chunk_size = 1400
        self.handler = handler

    # クライアントを起動してサーバ接続を行う関数
    def start(self):
        try:
            self.sock.connect((self.server_address, self.server_port))
            self.upload_file()
        except socket.error as err:
            print(err)
            sys.exit(1)
        finally:
            print('closing socket')
            self.sock.close()

    # ファイルをアップロードするメイン関数
    def upload_file(self):
        try:
            file_path = self.handler.input_file_path()
            _, media_type = os.path.splitext(file_path)
            media_type_bytes = media_type.encode('utf-8')

            with open(file_path, 'rb') as f:
                f.seek(0, os.SEEK_END)
                file_size = f.tell()
                f.seek(0)

                file_name = os.path.basename(f.name)
                operation = self.handler.input_operation()
                json_file = {'file_name': file_name, 'operation': operation}
                json_file = self.handler.input_operation_details(operation, json_file, file_path)

                json_bytes = json.dumps(json_file).encode('utf-8')
                header = self.prepare_upload_header(len(json_bytes), len(media_type_bytes), file_size)
                self.sock.sendall(header)
                self.sock.sendall(json_bytes + media_type_bytes)

                self.send_file_data(f)

                response = self.sock.recv(16)
                if int.from_bytes(response, 'big') != 0x00:
                    print("アップロードに失敗しました")
                    sys.exit(1)
                else:
                    print("アップロードに成功しました")

            self.receive_file()

        except Exception as e:
            print(f"エラーが発生しました: {e}")
            sys.exit(1)

    # ファイルデータをチャンク単位で送信する関数
    def send_file_data(self, file_obj):
        data = file_obj.read(self.chunk_size)
        while data:
            self.sock.send(data)
            data = file_obj.read(self.chunk_size)

    # ファイルダウンロードを開始する関数
    def receive_file(self):
        header = self.receive_response_header()
        self.handle_response_body(header)

    # サーバからレスポンスヘッダーを受信する関数
    def receive_response_header(self):
        header = self.sock.recv(8)
        return {
            'json_length': int.from_bytes(header[0:2], 'big'),
            'media_type_length': int.from_bytes(header[2:3], 'big'),
            'file_size': int.from_bytes(header[3:8], 'big')
        }

    # サーバからレスポンスボディを受信しファイルを保存する関数
    def handle_response_body(self, header_info):
        body = self.sock.recv(header_info['json_length'] + header_info['media_type_length'])
        json_file = json.loads(body[:header_info['json_length']].decode('utf-8'))

        if json_file['error']:
            print("サーバー側でエラーが発生しました:", json_file['error_message'])
            sys.exit(1)

        file_name = json_file['file_name']
        self.handler.save_received_file(file_name, self.sock, header_info['file_size'], self.chunk_size)

    # アップロード用ヘッダーを作成する関数
    def prepare_upload_header(self, json_length, media_type_length, payload_length):
        return json_length.to_bytes(2, 'big') + media_type_length.to_bytes(1, 'big') + payload_length.to_bytes(5, 'big')


if __name__ == "__main__":
    server_address = '0.0.0.0'
    tcp_server_port = 9001
    handler = FileHandler()
    client = TCPClient(server_address, tcp_server_port, handler)
    client.start()
