import socket
import threading
import os
import sys
import time
import json
import uuid
import base64
import zipfile
import subprocess
from connection import send_json, receive_json
from protocol import build_message, parse_message
from config import (
    PEER_HOST, 
    PEER_PORT,
    DISCOVERY_PORT,
    BUFFER_SIZE,
    ENCODING,
    EDGE_NODE_PORT,
    EDGE_NODE_HOST,
    WORK_DIR,
    UPDATE_INTERVAL,
    HEARTBEAT_INTERVAL
)

# Generate a unique peer ID if not provided
PEER_ID = str(uuid.uuid4())

class Peer:
    def __init__(self):
        self.master_ip = None
        self.master_port = None
        self.peer_id = PEER_ID
        self.work_dir = WORK_DIR
        os.makedirs(self.work_dir, exist_ok=True)

    def discover_master(self):
        """Discover master node using UDP broadcast."""
        print(f"[PEER {self.peer_id}] Discovering master...")
        
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        discover_msg = build_message("DISCOVER_MASTER", {
            "peer_id": self.peer_id,
            "port": PEER_PORT
        })
        
        while not self.master_ip:
            try:
                # Broadcast discovery message
                udp_sock.sendto(json.dumps(discover_msg).encode(ENCODING), ('<broadcast>', DISCOVERY_PORT))
                
                # Wait for response
                udp_sock.settimeout(5)
                data, addr = udp_sock.recvfrom(BUFFER_SIZE)
                msg_type, data = parse_message(json.loads(data.decode(ENCODING)))
                
                if msg_type == "MASTER_ANNOUNCE":
                    self.master_ip = data.get("master_ip")
                    self.master_port = data.get("master_port")
                    print(f"[PEER {self.peer_id}] Master found at {self.master_ip}:{self.master_port}")
                    return True
                    
            except socket.timeout:
                print(f"[PEER {self.peer_id}] No master response, retrying...")
            except Exception as e:
                print(f"[PEER {self.peer_id}] Discovery error: {e}")
                time.sleep(5)
        
        return False

    def register_with_master(self):
        """Register peer with the master node."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.master_ip, self.master_port))
                msg = build_message("REGISTER", {
                    "peer_id": self.peer_id,
                    "host": PEER_HOST,
                    "port": PEER_PORT
                })
                send_json(s, msg)
                msg_type, data = parse_message(receive_json(s))
                if msg_type == "REGISTERED":
                    print(f"[PEER {self.peer_id}] Successfully registered with master")
                    return True
                else:
                    print(f"[PEER {self.peer_id}] Registration failed: {data.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"[PEER {self.peer_id}] Registration error: {e}")
        return False

    def send_heartbeat(self, interval=HEARTBEAT_INTERVAL):
        """Send periodic heartbeat to master."""
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((self.master_ip, self.master_port))
                    msg = build_message("HEARTBEAT", {
                        "peer_id": self.peer_id
                    })
                    send_json(s, msg)
                    msg_type, data = parse_message(receive_json(s))
                    if msg_type == "ALIVE":
                        print(f"[PEER {self.peer_id}] Heartbeat acknowledged")
            except Exception as e:
                print(f"[PEER {self.peer_id}] Heartbeat error: {e}")
            time.sleep(interval)

    def process_task(self, task_name, task_data_b64):
        """Process a received task package."""
        try:
            # Create task directory
            task_dir = os.path.join(self.work_dir, task_name.replace('.zip', ''))
            os.makedirs(task_dir, exist_ok=True)
            
            # Save and extract ZIP
            zip_path = os.path.join(task_dir, task_name)
            with open(zip_path, 'wb') as f:
                f.write(base64.b64decode(task_data_b64))
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(task_dir)
            
            # Execute main.py
            main_script = os.path.join(task_dir, 'main.py')
            if not os.path.exists(main_script):
                raise Exception("main.py not found in task package")
            
            # Run the script and capture output
            stdout_path = os.path.join(task_dir, 'stdout.txt')
            stderr_path = os.path.join(task_dir, 'stderr.txt')
            
            with open(stdout_path, 'w') as stdout_file, open(stderr_path, 'w') as stderr_file:
                process = subprocess.Popen(
                    [sys.executable, main_script],
                    stdout=stdout_file,
                    stderr=stderr_file,
                    cwd=task_dir
                )
                process.wait()
            
            # Create results ZIP
            results_name = f"results_{task_name}"
            results_path = os.path.join(self.work_dir, results_name)
            
            with zipfile.ZipFile(results_path, 'w') as zip_ref:
                zip_ref.write(stdout_path, 'stdout.txt')
                zip_ref.write(stderr_path, 'stderr.txt')
            
            # Read and encode results
            with open(results_path, 'rb') as f:
                results_data = base64.b64encode(f.read()).decode(ENCODING)
            
            return results_name, results_data
            
        except Exception as e:
            print(f"[PEER {self.peer_id}] Task processing error: {e}")
            return None, None

    def request_and_process_tasks(self):
        """Main loop for requesting and processing tasks."""
        while True:
            try:
                # Request task
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((self.master_ip, self.master_port))
                    msg = build_message("REQUEST_TASK", {
                        "peer_id": self.peer_id
                    })
                    send_json(s, msg)
                    msg_type, data = parse_message(receive_json(s))
                
                if msg_type == "TASK_PACKAGE":
                    task_name = data.get("task_name")
                    task_data = data.get("task_data")
                    print(f"[PEER {self.peer_id}] Received task: {task_name}")
                    
                    # Process task
                    results_name, results_data = self.process_task(task_name, task_data)
                    if results_name and results_data:
                        # Submit results
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.connect((self.master_ip, self.master_port))
                            msg = build_message("SUBMIT_RESULT", {
                                "peer_id": self.peer_id,
                                "result_name": results_name,
                                "result_data": results_data
                            })
                            send_json(s, msg)
                            msg_type, data = parse_message(receive_json(s))
                            if msg_type == "OK":
                                print(f"[PEER {self.peer_id}] Results submitted successfully")
                
            except Exception as e:
                print(f"[PEER {self.peer_id}] Task processing cycle error: {e}")
            
            time.sleep(UPDATE_INTERVAL)  # Wait before requesting next task

    def run(self):
        """Start the peer node."""
        # Discover master
        if not self.discover_master():
            print(f"[PEER {self.peer_id}] Failed to discover master")
            return
        
        # Register with master
        if not self.register_with_master():
            print(f"[PEER {self.peer_id}] Failed to register with master")
            return
        
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self.send_heartbeat, daemon=True)
        heartbeat_thread.start()
        
        # Start task processing
        self.request_and_process_tasks()

if __name__ == "__main__":
    peer = Peer()
    peer.run()
