import json
from config import BUFFER_SIZE, ENCODING

def send_json(conn, data):
    message = json.dumps(data).encode(ENCODING)
    conn.sendall(message)

def receive_json(conn):
    data = conn.recv(BUFFER_SIZE)
    return json.loads(data.decode(ENCODING))