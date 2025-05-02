# client.py

import socket
import os
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')

class FileHandler:
    # フォルダを作成し、受信ファイルの保存先を準備する
    def __init__(self, dpath='receive'):
        self.dpath = dpath
        os.makedirs(self.dpath, exist_ok=True)

    # サーバーから送られてきたファイルをチャンク単位で受信し、ディスクに保存する
    def save_received_file(self, file_name, connection, file_size, chunk_size=1400):
        output_file_path = os.path.join(self.dpath, file_name)
        with open(output_file_path, 'wb+') as f:
            while file_size > 0:
                data = connection.recv(min(file_size, chunk_size))
                f.write(data)
                file_size -= len(data)
        return output_file_path


class TCPClient:
    # サーバーへの接続設定とハンドラーの初期化
    def __init__(self, server_address, server_port, handler: FileHandler):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = server_address
        self.server_port = server_port
        self.chunk_size = 1400
        self.handler = handler

    # ファイルをサーバーにアップロードし、指定の処理を実行して結果を受信する
    def upload_and_process(self, file_path, operation, operation_details={}):
        self.sock.connect((self.server_address, self.server_port))

        _, media_type = os.path.splitext(file_path)
        media_type_bytes = media_type.encode('utf-8')

        with open(file_path, 'rb') as f:
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
            f.seek(0)

            file_name = os.path.basename(f.name)
            json_file = {'file_name': file_name, 'operation': operation}
            json_file.update(operation_details)

            json_bytes = json.dumps(json_file).encode('utf-8')
            header = self.prepare_upload_header(len(json_bytes), len(media_type_bytes), file_size)
            self.sock.sendall(header)
            self.sock.sendall(json_bytes + media_type_bytes)

            data = f.read(self.chunk_size)
            while data:
                self.sock.send(data)
                data = f.read(self.chunk_size)

            response = self.sock.recv(1)
            if response != bytes([0x00]):
                raise Exception("サーバーがエラーを返しました")

        return self.receive_file()

    # サーバーからの応答を受け取り、ファイルを復元して保存する
    def receive_file(self):
        header = self.sock.recv(8)
        json_length = int.from_bytes(header[0:2], 'big')
        media_type_length = int.from_bytes(header[2:3], 'big')
        file_size = int.from_bytes(header[3:8], 'big')

        body = self.sock.recv(json_length + media_type_length)
        json_file = json.loads(body[:json_length].decode('utf-8'))

        if json_file['error']:
            raise Exception(f"サーバーエラー: {json_file['error_message']}")

        file_name = json_file['file_name']
        received_file_path = self.handler.save_received_file(file_name, self.sock, file_size, self.chunk_size)
        self.sock.close()
        return received_file_path

    # アップロード時に送信するヘッダーを構築して返す
    def prepare_upload_header(self, json_length, media_type_length, payload_length):
        return (
            json_length.to_bytes(2, 'big') +
            media_type_length.to_bytes(1, 'big') +
            payload_length.to_bytes(5, 'big')
        )
