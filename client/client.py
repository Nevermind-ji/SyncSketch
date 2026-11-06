import socket
import threading
import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from common.protocol import encode_message, receive_message


HOST = "127.0.0.1"
PORT = 5000


def receive_messages(client_socket):
    while True:
        try:
            message = receive_message(client_socket)

            if message is None:
                print("\nServer disconnected.")
                break

            if message["type"] == "chat":
                print("\nReceived:", message["text"])

        except (OSError, ValueError):
            break


client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

print("Connected to SyncSketch server!")

# Start a background thread for receiving messages
receive_thread = threading.Thread(
    target=receive_messages,
    args=(client_socket,),
    daemon=True
)

receive_thread.start()

# Main thread sends messages
while True:
    text = input("Enter your message (exit to quit): ")

    if text.lower() == "exit":
        break

    message = {
        "type": "chat",
        "text": text
    }

    data = encode_message(message)
    # json.dumps()-converts message to json text and encod("utf-8") converts texts to bytes for TCP-->in common.py

    client_socket.sendall(data)

client_socket.close()
print("Disconnected.")