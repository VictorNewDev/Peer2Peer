# config.py (do edge)
EDGE_NODE_HOST = '127.0.0.1'
EDGE_NODE_PORT = 8000            # Porta TCP para registro e troca de mensagens
DISCOVERY_PORT = 50000           # Porta UDP para o service discovery
UPDATE_INTERVAL = 30

BUFFER_SIZE = 4096
ENCODING = 'utf-8'

# Diretórios para tarefas e resultados no Master (edge)
TASKS_DIR = 'tasks'
RESULTS_DIR = 'results'


