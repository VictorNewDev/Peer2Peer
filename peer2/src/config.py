import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Caso seja necessário, você pode definir um diretório de arquivos compartilhados para o peer2.
SHARED_FILES_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'shared_files'))

PEER_HOST = '127.0.0.1'
PEER_PORT = 9002  # Alterado para evitar conflito com o peer1

EDGE_NODE_HOST = '127.0.0.1'
EDGE_NODE_PORT = 8000

UPDATE_INTERVAL = 20

BUFFER_SIZE = 4096
ENCODING = 'utf-8'

HEARTBEAT_INTERVAL = 10

# Opcional: definir um PEER_ID único para o peer2, se não for informado via linha de comando.
PEER_ID = "peer2"
