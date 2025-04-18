import socket
import sys
import os
import json
import ffmpeg
import re

class FileHandler:
    def __init__(self, dpath='recieve'):
        self.dpath = dpath
        os.makedirs(self.dpath, exist_ok=True)

    def input_file_path(self):
        valid_extensions = ('.mp4', '.avi')
        while True:
            file_path = input("ファイルパスを入力してください（mp4、aviのいずれかの拡張子）: ")
            if file_path.endswith(valid_extensions):
                print(f"有効なファイルパスが入力されました: {file_path}")
                return file_path
            else:
                print("無効なファイル拡張子です。もう一度試してください。")

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

    def input_operation_details(self, operation, json_file, file_path):
        if operation == 2:
            resolutions = {"1": "1920:1080", "2": "1280:720", "3": "720:480"}
            while True:
                print("1: フルHD(1920:1080), 2: HD(1280:720), 3: SD(720:480)")
                resolution = input("希望する解像度の番号を入力してください: ")
                if resolution in resolutions:
                    json_file['resolution'] = resolutions[resolution]
                    break
                else:
                    print("無効な選択です。もう一度入力してください。")

        elif operation == 3:
            aspect_ratios = {"1": "16/9", "2": "4/3", "3": "1/1"}
            while True:
                print("1: (16:9), 2: (4:3), 3: (1:1)")
                aspect_ratio = input("希望するアスペクト比の番号を入力してください: ")
                if aspect_ratio in aspect_ratios:
                    json_file['aspect_ratio'] = aspect_ratios[aspect_ratio]
                    break
                else:
                    print("無効な選択です。もう一度入力してください。")

        elif operation == 5:
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
                        json_file['start_time'] = start_time_sec
                        break
                    else:
                        print("開始時間は動画の長さより短くしてください。")
                else:
                    print("無効な時間形式です。もう一度入力してください。")

            while True:
                duration = input("再生時間を秒単位で入力してください（例: 10）: ")
                if duration.isdigit():
                    duration = float(duration)
                    if 0 < duration <= (video_duration - json_file['start_time']):
                        json_file['duration'] = duration
                        break
                    else:
                        print("無効な再生時間です。もう一度入力してください。")
                else:
                    print("無効な入力です。数字を入力してください。")
        return json_file

    def get_video_duration(self, file_path):
        probe = ffmpeg.probe(file_path)
        return float(probe['format']['duration'])

    def save_received_file(self, file_name, connection, file_size, chunk_size=1400):
        output_file_path = os.path.join(self.dpath, file_name)
        with open(output_file_path, 'wb+') as f:
            while file_size > 0:
                data = connection.recv(min(file_size, chunk_size))
                f.write(data)
                file_size -= len(data)
        print("ダウンロードに成功しました: ", output_file_path)


class TCPClient:
    def __init__(self, server_address, server_port, handler: FileHandler):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = server_address
        self.server_port = server_port
        self.chunk_size = 1400
        self.handler = handler

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
                header = self.build_header(len(json_bytes), len(media_type_bytes), file_size)
                self.sock.sendall(header)
                self.sock.sendall(json_bytes + media_type_bytes)

                data = f.read(self.chunk_size)
                while data:
                    self.sock.send(data)
                    data = f.read(self.chunk_size)

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

    def receive_file(self):
        header = self.sock.recv(8)
        json_length = int.from_bytes(header[0:2], 'big')
        media_type_length = int.from_bytes(header[2:3], 'big')
        file_size = int.from_bytes(header[3:8], 'big')

        body = self.sock.recv(json_length + media_type_length)
        json_file = json.loads(body[:json_length].decode('utf-8'))

        if json_file['error']:
            print("サーバー側でエラーが発生しました:", json_file['error_message'])
            sys.exit(1)

        file_name = json_file['file_name']
        self.handler.save_received_file(file_name, self.sock, file_size, self.chunk_size)

    def build_header(self, json_length, media_type_length, payload_length):
        return json_length.to_bytes(2, 'big') + media_type_length.to_bytes(1, 'big') + payload_length.to_bytes(5, 'big')


if __name__ == "__main__":
    server_address = '0.0.0.0'
    tcp_server_port = 9001
    handler = FileHandler()
    client = TCPClient(server_address, tcp_server_port, handler)
    client.start()
