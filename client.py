import socket
import os
import json
import sys
import logging
from pathlib import Path
import ffmpeg
import re

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(message)s')

# ファイル操作（アップロード用ファイル選択・オプション指定・保存）を担当するクラス
class FileHandler:

    def __init__(self, dpath='receive'):
        self.dpath = dpath
        os.makedirs(self.dpath, exist_ok=True)
        logging.info("\n=============================================")
        logging.info(f"\n📂 ディレクトリを作成/確認しました: {self.dpath}")

    def input_file_path(self):
        valid_extensions = ('.mp4', '.avi')
        while True:
            file_path = input("ファイルパスを入力してください（mp4、avi）: ")
            if file_path.endswith(valid_extensions):
                logging.info("\n=============================================")
                logging.info(f"\n📄 有効なファイルパスが入力されました: {file_path}")
                return file_path
            else:
                logging.warning("❌ 無効なファイル拡張子です。もう一度試してください。")

    def input_operation(self):
        while True:
            logging.info("")
            print("1: 動画の圧縮\n"
                  "2: 解像度変更\n"
                  "3: アスペクト比変更\n"
                  "4: 音声変換\n"
                  "5: GIF作成")

            try:
                logging.info("")
                operation = int(input("オペレーションを入力してください(1-5): "))
                if operation in range(1, 6):
                    logging.info("\n---------------------------------------------")
                    logging.info(f"\n🎛️ 選択されたオペレーション: {operation}")
                    return operation
                else:
                    logging.warning("❌ 無効な選択です。1から5の間で選択してください。")
            except ValueError:
                logging.warning("❌ 無効な入力です。数字を入力してください。")

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

    def input_resolution(self):
        resolutions = {"1": "1920:1080", "2": "1280:720", "3": "720:480"}
        while True:
            logging.info("")
            print("1: フルHD(1920:1080)\n"
                  "2: HD(1280:720)\n"
                  "3: SD(720:480)")

            logging.info("")
            resolution = input("解像度を選択してください: ")
            if resolution in resolutions:
                return resolutions[resolution]
            else:
                logging.warning("❌ 無効な解像度選択です。")

    def input_aspect_ratio(self):
        aspect_ratios = {"1": "16/9", "2": "4/3", "3": "1/1"}
        while True:
            logging.info("")
            print("1: (16:9)\n"
                  "2: (4:3)\n"
                  "3: (1:1)")

            logging.info("")
            aspect_ratio = input("アスペクト比を選択してください: ")
            if aspect_ratio in aspect_ratios:
                return aspect_ratios[aspect_ratio]
            else:
                logging.warning("❌ 無効なアスペクト比選択です。")

    def input_gif_time_range(self, file_path):
        video_duration = self.get_video_duration(file_path)
        HH = video_duration // 3600
        MM = (video_duration % 3600) // 60
        SS = video_duration % 60
        logging.info(f"動画の長さ: {int(HH):02}:{int(MM):02}:{int(SS):02}")
        while True:
            start_time = input("開始時間 (例: 00:00:10): ")
            if re.match(r'^\d{2}:\d{2}:\d{2}$', start_time):
                st_HH, st_MM, st_SS = map(int, start_time.split(":"))
                start_time_sec = st_HH * 3600 + st_MM * 60 + st_SS
                if start_time_sec < video_duration:
                    break
                else:
                    logging.warning("❌ 開始時間は動画の長さより短く設定してください。")
            else:
                logging.warning("❌ 無効な時間形式です。")

        while True:
            duration = input("再生時間（秒）: ")
            if duration.isdigit():
                duration = float(duration)
                if 0 < duration <= (video_duration - start_time_sec):
                    return start_time_sec, duration
                else:
                    logging.warning("❌ 無効な再生時間です。")
            else:
                logging.warning("❌ 数字で入力してください。")

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
        logging.info("\n---------------------------------------------")
        logging.info(f"\n📥 ファイルを保存しました: {output_file_path}")

class TCPClient:

    def __init__(self, server_address, server_port, handler: FileHandler):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = server_address
        self.server_port = server_port
        self.chunk_size = 1400
        self.handler = handler

    def start(self):
        try:
            # logging.info("\n=============================================")
            logging.info(f"📡 サーバーに接続中: {self.server_address}:{self.server_port}")
            self.sock.connect((self.server_address, self.server_port))
            self.upload_file()
        except socket.error as err:
            logging.error(f"❌ 接続エラー: {err}")
            sys.exit(1)
        finally:
            logging.info("🔌 ソケットを閉じます")
            logging.info("\n---------------------------------------------")
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
                header = self.prepare_upload_header(len(json_bytes), len(media_type_bytes), file_size)
                self.sock.sendall(header)
                self.sock.sendall(json_bytes + media_type_bytes)

                self.send_file_data(f)

                response = self.sock.recv(16)
                if int.from_bytes(response, 'big') != 0x00:
                    logging.error("❌ アップロードに失敗しました")
                    sys.exit(1)
                else:
                    # logging.info("\n---------------------------------------------")
                    logging.info("✅ アップロードに成功しました")

            self.receive_file()

        except Exception as e:
            logging.error(f"❌ エラーが発生しました: {e}")
            sys.exit(1)

    def send_file_data(self, file_obj):
        logging.info("\n📤 ファイル送信中...")
        data = file_obj.read(self.chunk_size)
        while data:
            self.sock.send(data)
            data = file_obj.read(self.chunk_size)
        logging.info("✅ ファイル送信完了")

    def receive_file(self):
        header = self.receive_response_header()
        self.handle_response_body(header)

    def receive_response_header(self):
        header = self.sock.recv(8)
        return {
            'json_length': int.from_bytes(header[0:2], 'big'),
            'media_type_length': int.from_bytes(header[2:3], 'big'),
            'file_size': int.from_bytes(header[3:8], 'big')
        }

    def handle_response_body(self, header_info):
        body = self.sock.recv(header_info['json_length'] + header_info['media_type_length'])
        json_file = json.loads(body[:header_info['json_length']].decode('utf-8'))

        if json_file['error']:
            logging.error(f"⚠️ サーバーエラー: {json_file['error_message']}")
            sys.exit(1)

        file_name = json_file['file_name']
        self.handler.save_received_file(file_name, self.sock, header_info['file_size'], self.chunk_size)

    def prepare_upload_header(self, json_length, media_type_length, payload_length):
        return json_length.to_bytes(2, 'big') + media_type_length.to_bytes(1, 'big') + payload_length.to_bytes(5, 'big')

if __name__ == "__main__":
    server_address = '0.0.0.0'
    tcp_server_port = 9001
    handler = FileHandler()
    client = TCPClient(server_address, tcp_server_port, handler)
    client.start()
