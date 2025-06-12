# edge/src/edge_node.py
import socket
import threading
import os
import base64
import json
import time
from connection import send_json, receive_json
from protocol import parse_message, build_message
from config import EDGE_NODE_PORT, BUFFER_SIZE, ENCODING, DISCOVERY_PORT, TASKS_DIR, RESULTS_DIR

# Dictionary to store registered peers
peer_registry = {}

def run_discovery():
    """UDP listener for service discovery."""
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reuse
    udp_sock.bind(("0.0.0.0", DISCOVERY_PORT))
    print(f"[MASTER] UDP listener active on port {DISCOVERY_PORT} for DISCOVER_MASTER")
    
    while True:
        try:
            data, addr = udp_sock.recvfrom(BUFFER_SIZE)
            msg = json.loads(data.decode(ENCODING))
            msg_type, msg_data = parse_message(msg)
            
            if msg_type == "DISCOVER_MASTER":
                peer_id = msg_data.get("peer_id")
                peer_port = msg_data.get("port")
                print(f"[MASTER] DISCOVER_MASTER received from peer {peer_id} at {addr}")
                
                response = build_message("MASTER_ANNOUNCE", {
                    "master_ip": socket.gethostbyname(socket.gethostname()),
                    "master_port": EDGE_NODE_PORT
                })
                udp_sock.sendto(json.dumps(response).encode(ENCODING), addr)
        except Exception as e:
            print(f"[MASTER] Error in discovery: {e}")

def handle_peer(conn):
    try:
        msg = receive_json(conn)
        msg_type, data = parse_message(msg)

        if msg_type == 'REGISTER':
            peer_id = data.get('peer_id')
            host = data.get('host')
            port = data.get('port')
            
            if host and port:
                peer_registry[peer_id] = {
                    "host": host,
                    "port": port,
                    "last_seen": time.time()
                }
                print(f"[MASTER] Peer registered: {peer_id}")
                response = build_message("REGISTERED", {})
                send_json(conn, response)
            else:
                response = build_message("ERROR", {"error": "Missing host or port"})
                send_json(conn, response)

        elif msg_type == 'HEARTBEAT':
            peer_id = data.get('peer_id')
            if peer_id in peer_registry:
                peer_registry[peer_id]["last_seen"] = time.time()
                print(f"[MASTER] Heartbeat received from {peer_id}")
                response = build_message("ALIVE", {})
                send_json(conn, response)
            else:
                response = build_message("ERROR", {"error": "Peer not registered"})
                send_json(conn, response)

        elif msg_type == "REQUEST_TASK":
            peer_id = data.get('peer_id')
            print(f"[MASTER] REQUEST_TASK received from {peer_id}")
            
            tasks = os.listdir(TASKS_DIR) if os.path.exists(TASKS_DIR) else []
            if tasks:
                task_name = tasks[0]  # Get first available task
                task_path = os.path.join(TASKS_DIR, task_name)
                with open(task_path, "rb") as f:
                    task_data = f.read()
                task_data_b64 = base64.b64encode(task_data).decode(ENCODING)
                
                response = build_message("TASK_PACKAGE", {
                    "task_name": task_name,
                    "task_data": task_data_b64
                })
                send_json(conn, response)
                # Move or delete task after assignment
                os.remove(task_path)
            else:
                response = build_message("NO_TASKS", {})
                send_json(conn, response)

        elif msg_type == "SUBMIT_RESULT":
            peer_id = data.get('peer_id')
            result_name = data.get("result_name")
            result_data_b64 = data.get("result_data")
            
            print(f"[MASTER] SUBMIT_RESULT received from {peer_id}")
            
            result_bytes = base64.b64decode(result_data_b64.encode(ENCODING))
            os.makedirs(RESULTS_DIR, exist_ok=True)
            result_path = os.path.join(RESULTS_DIR, result_name)
            
            with open(result_path, "wb") as f:
                f.write(result_bytes)
            print(f"[MASTER] Result saved: {result_path}")
            
            response = build_message("OK", {})
            send_json(conn, response)

    except Exception as e:
        print(f"[MASTER] Error handling peer: {e}")
        try:
            response = build_message("ERROR", {"error": str(e)})
            send_json(conn, response)
        except:
            pass
    finally:
        conn.close()

def run_tcp():
    """Run TCP server for peer connections."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reuse
    server.bind(("0.0.0.0", EDGE_NODE_PORT))
    server.listen(5)
    print(f"[MASTER] Active on TCP port {EDGE_NODE_PORT}...")
    
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_peer, args=(conn,), daemon=True).start()

def run_edge():
    """Initialize and run the master node."""
    # Ensure required directories exist
    os.makedirs(TASKS_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Start UDP discovery service
    udp_thread = threading.Thread(target=run_discovery, daemon=True)
    udp_thread.start()
    
    # Run main TCP server
    run_tcp()

if __name__ == "__main__":
    run_edge()
