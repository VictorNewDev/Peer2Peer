import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_FILES_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'shared_files'))  # se necessário para outros propósitos

PEER_HOST = '127.0.0.1'
PEER_PORT = 9001

EDGE_NODE_HOST = '127.0.0.1'
EDGE_NODE_PORT = 8000  # Mesmo definido no config do edge

UPDATE_INTERVAL = 20
HEARTBEAT_INTERVAL = 10

BUFFER_SIZE = 4096
ENCODING = 'utf-8'
