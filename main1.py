import os
import io
import json
import socket
import pathlib
import mimetypes
import urllib.parse
from threading import Thread
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler


BASE_DIR = pathlib.Path()


class HttpGetHandler(BaseHTTPRequestHandler):
    
    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        data_parse = urllib.parse.unquote_plus(data.decode())
        self.save_data_via_socket(data_parse)
        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        match pr_url.path:
            case '/':
                self.send_html_file('index.html')
            case '/message':
                self.send_html_file('message.html')
            case _:
                file = BASE_DIR.joinpath(pr_url.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        with open(filename, 'rb') as fd:
            response_content = fd.read()
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', str(len(response_content)))
        self.end_headers()
        self.wfile.write(response_content)

    def send_static(self, file):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header('Content-type', mt[0])
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(file, 'rb') as fd:  # ./assets/js/app.js
            self.wfile.write(fd.read())

    def save_data_via_socket(self, send_data):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server = host, port
        data = send_data.encode()
        sock.sendto(data, server)
        sock.close()

# host = socket.gethostbyname(socket.gethostname())
host = '127.0.0.1'
port = 5000
# print(host)

def run(server_class=HTTPServer, handler_class=HttpGetHandler):
    print('Start server')
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        start_server = Thread(target=server)
        start_server.start()
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

if os.path.isfile(BASE_DIR.joinpath('storage/data.json')) and os.access(BASE_DIR.joinpath('storage/data.json'), os.R_OK):
    # checks if file exists
    print ("File exists and is readable")
else:
    print ("Either file is missing or is not readable, creating file...")
    with io.open(os.path.join(BASE_DIR.joinpath('storage'), 'data.json'), 'w') as db_file:
        db_file.write(json.dumps({}))

def save_data_to_json(data, time_data):
    data_parse = urllib.parse.unquote_plus(data.decode())
    data_parse = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
    # print(data_parse)

    with open('storage/data.json') as json_file:
        json_decoded = json.load(json_file)
        json_decoded[time_data] = data_parse
            
        with open('storage/data.json', 'w') as json_1:
            json.dump(json_decoded, json_1)

def server():
    print("Start server socket")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    print(f'Connection from {host}')
    while True:
        message, address = server_socket.recvfrom(1024)
        # print(f'========================{message}=================')
        time_data = str(datetime.now())
        save_data_to_json(message, time_data)
        if not message:
            break
        # print(f'received message: {message}')
    server_socket.close()


if __name__ == '__main__':
    run()
