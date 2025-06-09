# edge/src/edge_node.py
import socket
import threading
import os
import base64
from connection import send_json, receive_json
from protocol import parse_message, build_message
from config import EDGE_NODE_PORT, BUFFER_SIZE, ENCODING, DISCOVERY_PORT, TASKS_DIR, RESULTS_DIR

# Dicionário para registrar os peers
peer_registry = {}


def run_discovery():
    """Listener UDP para service discovery."""
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(("", DISCOVERY_PORT))
    print(f"[EDGE] Listener UDP ativo na porta {DISCOVERY_PORT} para DISCOVER_MASTER.")
    while True:
        data, addr = udp_sock.recvfrom(BUFFER_SIZE)
        try:
            msg = data.decode(ENCODING)
            import json
            msg_dict = json.loads(msg)
            if msg_dict.get("action") == "DISCOVER_MASTER":
                print(f"[EDGE] DISCOVER_MASTER recebido de {addr}")
                response = {
                    "action": "MASTER_ANNOUNCE",
                    "master_ip": socket.gethostbyname(socket.gethostname()),
                    "master_port": EDGE_NODE_PORT
                }
                udp_sock.sendto(json.dumps(response).encode(ENCODING), addr)
        except Exception as e:
            print(f"[EDGE] Erro no discovery: {e}")


def handle_peer(conn):
    try:
        msg = receive_json(conn)
        msg_type, data = parse_message(msg)

        # Trata registro e heartbeat
        if msg_type in ['REGISTER', 'HEARTBEAT']:
            peer_id = data['peer_id']
            host = data['host']
            port = data['port']
            # Armazena também os arquivos enviados com o registro
            peer_registry[peer_id] = {
                "host": host,
                "port": port,
                "files": data.get("files", [])
            }
            if msg_type == 'REGISTER':
                print(f"[EDGE] Peer registrado: {peer_id} com arquivos {data.get('files', [])}")
                response = build_message("REGISTERED", {"status": "REGISTERED"})
            else:
                print(f"[EDGE] Heartbeat recebido de {peer_id}")
                response = build_message("ALIVE", {"status": "ALIVE"})
            send_json(conn, response)

        # Trata solicitação de tarefa
        elif msg_type == "REQUEST_TASK":
            print(f"[EDGE] REQUEST_TASK recebido de {data.get('peer_id')}")
            tasks = os.listdir(TASKS_DIR) if os.path.exists(TASKS_DIR) else []
            if tasks:
                task_name = tasks[0]
                task_path = os.path.join(TASKS_DIR, task_name)
                with open(task_path, "rb") as f:
                    task_data = f.read()
                task_data_b64 = base64.b64encode(task_data).decode(ENCODING)
                response = {
                    "action": "TASK_PACKAGE",
                    "task_name": task_name,
                    "task_data": task_data_b64
                }
            else:
                response = {"action": "NO_TASK", "message": "Nenhuma tarefa disponível"}
            send_json(conn, response)

        # Trata submissão de resultado
        elif msg_type == "SUBMIT_RESULT":
            print(f"[EDGE] SUBMIT_RESULT recebido de {data.get('peer_id')}")
            result_name = data.get("result_name")
            result_data_b64 = data.get("result_data")
            result_bytes = base64.b64decode(result_data_b64.encode(ENCODING))
            os.makedirs(RESULTS_DIR, exist_ok=True)
            result_path = os.path.join(RESULTS_DIR, result_name)
            with open(result_path, "wb") as f:
                f.write(result_bytes)
            print(f"[EDGE] Resultado salvo: {result_path}")
            response = {"status": "OK"}
            send_json(conn, response)

        # Trata solicitação de listagem dos arquivos de um peer (LIST_FILES)
        elif msg_type == "LIST_FILES":
            target_peer = data.get("target_peer_id")
            if target_peer in peer_registry:
                files = peer_registry[target_peer].get("files", [])
                response = build_message("FILES_LIST", {"peer_id": target_peer, "files": files})
            else:
                response = build_message("PEER_NOT_FOUND", {"peer_id": target_peer})
            send_json(conn, response)

        # > NOVO: Trata a solicitação para encontrar um arquivo (FIND_FILE)
        elif msg_type == "FIND_FILE":
            filename = data.get("filename")
            peers_with_file = []
            for peer_id, peer_data in peer_registry.items():
                for f in peer_data.get("files", []):
                    if f.get("name") == filename:
                        peers_with_file.append({
                            "peer_id": peer_id,
                            "host": peer_data.get("host"),
                            "port": peer_data.get("port")
                        })
            if peers_with_file:
                response = build_message("FILE_LOCATION", {"peers": peers_with_file})
            else:
                response = build_message("FILE_NOT_FOUND", {"filename": filename})
            send_json(conn, response)

        else:
            print(f"[EDGE] Ação não reconhecida: {msg_type}")

    except Exception as e:
        print(f"[EDGE] Erro ao lidar com o peer: {e}")
    finally:
        conn.close()


def run_tcp():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("", EDGE_NODE_PORT))
    server.listen(5)
    print(f"[EDGE] Nó de borda (Master) ativo na porta TCP {EDGE_NODE_PORT}...")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_peer, args=(conn,), daemon=True).start()


def run_edge():
    os.makedirs(TASKS_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    udp_thread = threading.Thread(target=run_discovery, daemon=True)
    udp_thread.start()
    run_tcp()


if __name__ == "__main__":
    run_edge()
