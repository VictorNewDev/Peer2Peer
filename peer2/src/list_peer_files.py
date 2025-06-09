# peer1/src/list_peer_files.py

import socket
from connection import send_json, receive_json
from protocol import build_message, parse_message
from config import EDGE_NODE_HOST, EDGE_NODE_PORT, BUFFER_SIZE, ENCODING

def list_peer_files(target_peer_id):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((EDGE_NODE_HOST, EDGE_NODE_PORT))
        # Envia mensagem LIST_FILES com o ID do peer alvo
        msg = build_message("LIST_FILES", {"target_peer_id": target_peer_id})
        send_json(s, msg)
        response = receive_json(s)
    msg_type, data = parse_message(response)
    if msg_type == "FILES_LIST":
        print(f"Arquivos do peer '{data['peer_id']}':")
        files = data.get("files", [])
        if files:
            for f in files:
                print(f" - {f['name']} (checksum: {f['checksum']})")
        else:
            print("Nenhum arquivo encontrado.")
    elif msg_type == "PEER_NOT_FOUND":
        print(f"Peer '{data['peer_id']}' não encontrado.")
    else:
        print("Resposta inesperada:", response)

if __name__ == "__main__":
    target = input("Digite o ID do peer para ver seus arquivos (ex.: peer2): ")
    list_peer_files(target)
