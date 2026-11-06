import socket
import threading
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from common.protocol import encode_message, receive_message

HOST = "127.0.0.1"
PORT = 5000

connected_clients = []
drawing_history = []
clients_lock = threading.Lock()

def broadcast(message, sender_socket):

    with clients_lock:
        for client in connected_clients:

            # Don't send the message back to its sender
            if client != sender_socket:
                try:
                    client.sendall(message)

                except OSError:
                    print("Could not send message to a client")

def handle_client(client_socket, client_address):

    print(f"Connected: {client_address}")

    # Send existing drawing history to the new client
    for drawing in drawing_history:
        data = encode_message(drawing)
        client_socket.sendall(data)

    # Add client to shared list
    with clients_lock:
        connected_clients.append(client_socket)

    try:
        while True:
            message = receive_message(client_socket)

            if message is None:
                break

            print(f"Received from {client_address}: {message}")

# Store drawing events
            if message["type"] == "draw":
                drawing_history.append(message)

# Clear drawing history when canvas is cleared
            elif message["type"] == "clear":
                 drawing_history.clear()

            data = encode_message(message)

            broadcast(data, client_socket)

    except ConnectionError:
        print(f"Connection lost: {client_address}")

    finally:
        # Remove disconnected client
        with clients_lock:
            if client_socket in connected_clients:
                connected_clients.remove(client_socket)

        client_socket.close()
        print(f"Disconnected: {client_address}")


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((HOST, PORT))
server_socket.listen()

print(f"Server running on {HOST}:{PORT}")

while True:
    client_socket, client_address = server_socket.accept()

    client_thread = threading.Thread(
        target=handle_client,
        args=(client_socket, client_address)
    )

    client_thread.start()