import socket
import threading
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class ChatClient:
    def __init__(self, host='127.0.0.1', port=5000):
        """
        Initializes the client:
        - Creates a socket and connects to the chat server.
        - Prompts the user for a name.
        - Sends the username to the server.
        - Starts a listener thread to receive messages.
        - Starts sending messages in the main thread.
        """
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port))
        except Exception as e:
            logging.error("Unable to connect to server: %s", e)
            return

        self.name = input("Enter your name: ")
        self.client_socket.send(self.name.encode('utf-8'))
        logging.info("Connected to chat server at %s:%d as %s", self.host, self.port, self.name)

        threading.Thread(target=self.receive_messages, daemon=True).start()
        self.send_messages()

    def receive_messages(self):
        """
        Continuously listens for incoming messages from the server.
        Prints the messages to the console.
        If the server disconnects or an error occurs, the client exits.
        """
        while True:
            try:
                server_message = self.client_socket.recv(1024).decode('utf-8')
                if not server_message.strip():
                    logging.warning("Server closed the connection.")
                    os._exit(0)
                print(server_message)
            except ConnectionError:
                logging.warning("Connection lost to server.")
                os._exit(0)
            except Exception as e:
                logging.error("Error receiving message: %s", e)
                os._exit(0)

    def send_messages(self):
        """
        Continuously reads user input and sends messages to the server.
        Type `/quit` to leave the chat gracefully.
        """
        try:
            while True:
                client_input = input()
                if client_input.lower() == "/quit":
                    logging.info("You have left the chat.")
                    self.client_socket.close()
                    os._exit(0)

                client_message = f"{self.name}: {client_input}"
                try:
                    self.client_socket.send(client_message.encode('utf-8'))
                except ConnectionError:
                    logging.warning("Unable to send. Server disconnected!")
                    os._exit(0)
        except KeyboardInterrupt:
            logging.info("Chat client terminated by user.")
            try:
                self.client_socket.close()
            except:
                pass
            os._exit(0)

if __name__ == "__main__":
    ChatClient()

