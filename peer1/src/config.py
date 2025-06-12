import os
import socket

# Network settings
PEER_HOST = socket.gethostbyname(socket.gethostname())
PEER_PORT = 55002  # Each peer should use a different port
DISCOVERY_PORT = 55001  # Must match the edge node's discovery port
BUFFER_SIZE = 4096
ENCODING = 'utf-8'

# Edge node settings (only used as fallback if discovery fails)
EDGE_NODE_HOST = socket.gethostbyname(socket.gethostname())  # Will be discovered automatically
EDGE_NODE_PORT = 55000  # Must match edge node's port

# Directory settings
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = os.path.join(BASE_DIR, "work")  # Directory for task processing

# Intervals
UPDATE_INTERVAL = 20
HEARTBEAT_INTERVAL = 10
