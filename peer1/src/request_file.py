import socket
import os
from connection import send_json, receive_json
from protocol import build_message
from config import EDGE_NODE_HOST, EDGE_NODE_PORT, SHARED_FILES_DIR, BUFFER_SIZE


def request_file(filename):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((EDGE_NODE_HOST, EDGE_NODE_PORT))
        msg = build_message("FIND_FILE", {"filename": filename})
        send_json(s, msg)
        response = receive_json(s)

    response_type = response.get("type")
    if response_type == "FILE_NOT_FOUND":
        print(f"[!] Nenhum peer possui o arquivo '{filename}'.")
        return

    peers = response.get("data", {}).get("peers", [])
    if not peers:
        print(f"[!] Nenhum peer possui o arquivo '{filename}'.")
        return

    peer = peers[0]
    peer_host = peer["host"]
    peer_port = peer["port"]
    print(f"[+] Arquivo encontrado em {peer_host}:{peer_port}, baixando...")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ps:
        ps.connect((peer_host, peer_port))
        msg = build_message("GET_FILE", {"filename": filename})
        send_json(ps, msg)

        path = os.path.join(SHARED_FILES_DIR, filename)
        with open(path, "wb") as f:
            while True:
                data = ps.recv(BUFFER_SIZE)
                if not data:
                    break
                f.write(data)

    print(f"[✓] Arquivo '{filename}' salvo em {path}")


if __name__ == "__main__":
    file_name = input("Digite o nome do arquivo que deseja baixar: ")
    request_file(file_name)
