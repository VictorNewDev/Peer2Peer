import json
from config import BUFFER_SIZE, ENCODING

def send_json(conn, data):
    message = json.dumps(data).encode(ENCODING)
    conn.sendall(message)

def receive_json(conn):
    chunks = []
    while True:
        chunk = conn.recv(BUFFER_SIZE)
        if not chunk:
            break
        chunks.append(chunk)
        try:
            return json.loads(b''.join(chunks).decode(ENCODING))
        except json.JSONDecodeError:
            # If we can't decode yet, continue receiving
            continue
    
    # If we get here, the connection was closed before receiving a valid JSON
    raise ConnectionError("Connection closed before receiving complete message")