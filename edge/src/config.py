# config.py (edge node)
import socket

# Network settings
EDGE_NODE_HOST = socket.gethostbyname(socket.gethostname())  # Get actual IP
EDGE_NODE_PORT = 55000  # TCP port for registration and message exchange
DISCOVERY_PORT = 55001  # UDP port for service discovery (must match peers)
UPDATE_INTERVAL = 30

BUFFER_SIZE = 4096
ENCODING = 'utf-8'

# Directories for tasks and results
TASKS_DIR = 'tasks'
RESULTS_DIR = 'results'


