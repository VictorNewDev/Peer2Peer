import socket
import threading
import os
import sys
import time
from connection import send_json, receive_json
from protocol import build_message, parse_message
from files_utils import list_files, calculate_checksum
from config import PEER_HOST, PEER_PORT, EDGE_NODE_HOST, EDGE_NODE_PORT, SHARED_FILES_DIR, ENCODING

# Obtém o PEER_ID, ou define como o hostname se não for passado via argumento ou no config
try:
    from config import PEER_ID
except ImportError:
    PEER_ID = socket.gethostname()

def handle_request(conn):
    """Função que lida com requisições de arquivos de outros peers."""
    try:
        msg = receive_json(conn)
        msg_type, data = parse_message(msg)

        if msg_type == 'GET_FILE':
            filename = data.get('filename')
            path = os.path.join(SHARED_FILES_DIR, filename)
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    conn.sendfile(f)
            else:
                print(f"[PEER {PEER_ID}] Arquivo não encontrado: {filename}")
    except Exception as e:
        print(f"[PEER {PEER_ID}] Erro em handle_request: {e}")
    finally:
        conn.close()

def serve():
    """Inicia o servidor que atende solicitações de outros peers (GET_FILE, etc.)."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((PEER_HOST, PEER_PORT))
    server.listen(5)
    print(f"[PEER {PEER_ID}] Aguardando conexões em {PEER_HOST}:{PEER_PORT}...")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_request, args=(conn,), daemon=True).start()

def register_with_edge():
    """Registra o peer e a lista de arquivos disponíveis com o nó de borda."""
    if not os.path.exists(SHARED_FILES_DIR):
        print(f"[PEER {PEER_ID}] Diretório de arquivos compartilhados não encontrado: {SHARED_FILES_DIR}")
        return

    files = list_files(SHARED_FILES_DIR)
    print(f"[PEER {PEER_ID}] Diretório SHARED_FILES: {SHARED_FILES_DIR}")
    print(f"[PEER {PEER_ID}] Arquivos detectados: {files}")  # Debug

    file_data = [{"name": f, "checksum": calculate_checksum(os.path.join(SHARED_FILES_DIR, f))} for f in files]
    print(f"[PEER {PEER_ID}] Dados dos arquivos a enviar: {file_data}")  # Debug

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((EDGE_NODE_HOST, EDGE_NODE_PORT))
            msg = build_message("REGISTER", {
                "peer_id": PEER_ID,
                "host": PEER_HOST,
                "port": PEER_PORT,
                "files": file_data
            })
            send_json(s, msg)
            response = receive_json(s)
            if response.get("status") == "REGISTERED":
                print(f"[PEER {PEER_ID}] Registro efetuado com sucesso.")
            else:
                print(f"[PEER {PEER_ID}] Erro no registro: ", response)
    except Exception as e:
        print(f"[PEER {PEER_ID}] Exceção no registro: {e}")

def send_heartbeat(interval=10):
    """Envia periodicamente um heartbeat com informações atualizadas dos arquivos."""
    while True:
        try:
            files = list_files(SHARED_FILES_DIR)
            file_data = [{"name": f, "checksum": calculate_checksum(os.path.join(SHARED_FILES_DIR, f))} for f in files]
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((EDGE_NODE_HOST, EDGE_NODE_PORT))
                msg = build_message("HEARTBEAT", {
                    "peer_id": PEER_ID,
                    "host": PEER_HOST,
                    "port": PEER_PORT,
                    "files": file_data
                })
                send_json(s, msg)
            print(f"[PEER {PEER_ID}] Enviou heartbeat com {len(files)} arquivo(s).")
        except Exception as e:
            print(f"[PEER {PEER_ID}] Erro ao enviar heartbeat: {e}")
        time.sleep(interval)
