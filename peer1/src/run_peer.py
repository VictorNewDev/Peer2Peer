from regular_node import serve, register_with_edge, send_heartbeat
import threading

if __name__ == '__main__':
    # Inicia o servidor numa thread separada
    server_thread = threading.Thread(target=serve)
    server_thread.start()

    # Registra o peer no nó de borda
    register_with_edge()

    # Inicia a thread que envia heartbeats periodicamente
    heartbeat_thread = threading.Thread(target=send_heartbeat, daemon=True)
    heartbeat_thread.start()

    # Aguarda o servidor rodar indefinidamente
    server_thread.join()
