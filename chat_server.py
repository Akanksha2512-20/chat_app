import socket
import threading
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class ChatServer:
    Clients = []
    Clients_lock = threading.Lock()

    def __init__(self, host='127.0.0.1', port=5000):
        """
        Initializes the chat server:
        - Creates a TCP socket.
        - Binds to the specified host and port.
        - Starts listening for incoming client connections.
        """
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        logging.info("Server is waiting for connections on %s:%d", self.host, self.port)

    def start(self):
        """
        Main server loop:
        - Accepts new client connections.
        - Receives the client's name.
        - Adds the client to the list of clients.
        - Starts a new thread to handle messages for each client.
        """
        while True:
            try:
                client_socket, address = self.server_socket.accept()
                logging.info("New connection from %s", address)

                client_name = client_socket.recv(1024).decode().strip()
                client = {"client_name": client_name, "client_socket": client_socket}

                self.broadcast_message(client_socket, f"{client_name} has joined the chat!")
                with self.Clients_lock:
                    self.Clients.append(client)

                threading.Thread(
                    target=self.handle_new_client,
                    args=(client,),
                    daemon=True
                ).start()
            except Exception as e:
                logging.error("Error accepting connection: %s", e, exc_info=True)

    def handle_new_client(self, client):
        """
        Handles an individual client's messages:
        - Receives messages.
        - Broadcasts them to other clients.
        - Removes the client if they disconnect or send a quit signal.
        """
        client_name = client["client_name"]
        client_socket = client["client_socket"]

        while True:
            try:
                client_message = client_socket.recv(1024).decode().strip()

                if not client_message or client_message.lower() == f"{client_name}bye":
                    self.broadcast_message(client_socket, f"{client_name} has left the chat")
                    with self.Clients_lock:
                        self.Clients.remove(client)
                    client_socket.close()
                    logging.info("%s has left the chat", client_name)
                    break
                else:
                    self.broadcast_message(client_socket, client_message)
            except ConnectionError:
                logging.warning("%s disconnected abruptly", client_name)
                with self.Clients_lock:
                    if client in self.Clients:
                        self.Clients.remove(client)
                client_socket.close()
                break
            except Exception as e:
                logging.error("Error handling client %s: %s", client_name, e, exc_info=True)

    def broadcast_message(self, sender_socket, message):
        """
        Sends a message to all clients except the sender:
        - Uses a lock for thread safety.
        - Closes and removes clients that cannot receive messages.
        """
        with self.Clients_lock:
            for client in self.Clients:
                client_socket = client['client_socket']
                if client_socket != sender_socket:
                    try:
                        client_socket.send(message.encode('utf-8'))
                    except BrokenPipeError:
                        logging.warning(
                            "Broken pipe to client %s, removing client",
                            client['client_name']
                        )
                        self.Clients.remove(client)
                        client_socket.close()

if __name__ == "__main__":
    server = ChatServer()
    server.start()
