import socket
import tkinter as tk
from tkinter import colorchooser, messagebox
import threading
import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from common.protocol import encode_message, receive_message



# Main window
root = tk.Tk()
root.title("SyncSketch")
root.geometry("1000x700")
root.minsize(700, 500)
root.configure(bg="#f0f2f5")

# Drawing state
current_color = "#000000"
current_tool = "pen"
last_x = None
last_y = None
is_drawing = False

# Header
header = tk.Frame(root, bg="#FFFFFF", height=65)
header.pack(fill="x")
header.pack_propagate(False)

tk.Label(
    header, text="SyncSketch",
    font=("Arial", 22, "bold"),
    fg="white", bg="#202b3c"
).pack(side="left", padx=20, pady=12)

tk.Label(
    header, text="Real-time collaborative whiteboard",
    font=("Arial", 10),
    fg="#FFFFFF", bg="#202b3c"
).pack(side="left", padx=10, pady=18)

# Toolbar
toolbar = tk.Frame(root, bg="white", padx=10, pady=10)
toolbar.pack(fill="x")

tk.Label(
    toolbar, text="Colour:",
    font=("Arial", 10, "bold"), bg="white"
).pack(side="left", padx=(5, 8))

# Status bar
status_label = tk.Label(
    root,
    text="Tool: Pen | Colour: #000000",
    anchor="w", bg="#e4e7eb", fg="#202b3c",
    padx=12, pady=7
)

def select_color(color):
    global current_color, current_tool

    current_color = color
    current_tool = "pen"
    status_label.config(text=f"Tool: Pen | Colour: {color}")

colors = [
    ("Black", "#000000"),
    ("Red", "#e53935"),
    ("Blue", "#1e88e5"),
    ("Green", "#43a047"),
    ("Purple", "#8e24aa"),
    ("Orange", "#fb8c00")
]

for name, value in colors:
    tk.Button(
        toolbar,
        text=name,
        bg=value, fg="white",
        activebackground=value,
        relief="flat", padx=8,
        command=lambda c=value: select_color(c)
    ).pack(side="left", padx=3)

def choose_custom_color():
    chosen = colorchooser.askcolor(
        color=current_color,
        title="Choose a drawing colour"
    )

    if chosen[1]:
        select_color(chosen[1])

tk.Button(
    toolbar, text="Custom Colour",
    command=choose_custom_color,
    relief="groove", padx=8
).pack(side="left", padx=6)

def activate_eraser():
    global current_tool
    current_tool = "eraser"
    status_label.config(text="Tool: Eraser")

tk.Button(
    toolbar, text="Eraser",
    command=activate_eraser,
    relief="groove", padx=10
).pack(side="left", padx=6)

# Canvas
canvas = tk.Canvas(
    root, bg="white", cursor="crosshair",
    highlightthickness=1,
    highlightbackground="#cbd5e1"
)
canvas.pack(fill="both", expand=True, padx=12, pady=10)

def clear_canvas():
    if messagebox.askyesno(
        "Clear Canvas",
        "Are you sure you want to clear the entire canvas?"
    ):
        canvas.delete("all")
        if client_socket:
            message = {
                "type": "clear"
            }

            client_socket.sendall(encode_message(message))
        status_label.config(text="Canvas cleared")

tk.Button(
    toolbar, text="Clear Canvas",
    command=clear_canvas,
    bg="#dc3545", fg="white",
    activebackground="#b02a37",
    relief="flat", padx=10
).pack(side="right", padx=5)

# Drawing events
def start_drawing(event):
    global last_x, last_y, is_drawing

    last_x, last_y = event.x, event.y
    is_drawing = True

def draw(event):
    global last_x, last_y

    if not is_drawing:
        return

    if current_tool == "eraser":
        drawing_color = "white"
        line_width = 20
    else:
        drawing_color = current_color
        line_width = 3

    canvas.create_line(
        last_x, last_y, event.x, event.y,
        fill=drawing_color,
        width=line_width,
        capstyle=tk.ROUND,
        smooth=True,
        splinesteps=36
    )
        # Send drawing event to server
    if client_socket:
        message = {
            "type": "draw",
            "x1": last_x,
            "y1": last_y,
            "x2": event.x,
            "y2": event.y,
            "color": drawing_color,
            "width": line_width
        }

        try:
            client_socket.sendall(encode_message(message))
        except OSError:
            status_label.config(text="Connection lost!")

    last_x, last_y = event.x, event.y

def draw_remote_line(message):

    canvas.create_line(
        message["x1"],
        message["y1"],
        message["x2"],
        message["y2"],
        fill=message["color"],
        width=message["width"],
        capstyle=tk.ROUND,
        smooth=True,
        splinesteps=36
    )


def receive_drawing():
    while True:
        try:
            message = receive_message(client_socket)

            if message is None:
                break

            if message["type"] == "draw":
                root.after(0, draw_remote_line, message)

            elif message["type"] == "clear":
                root.after(0, canvas.delete, "all")

        except (OSError, ValueError):
            break

    root.after(0, lambda: status_label.config(
        text="Disconnected from server"
    ))

def stop_drawing(event):
    global last_x, last_y, is_drawing

    is_drawing = False
    last_x, last_y = None, None

canvas.bind("<Button-1>", start_drawing)
canvas.bind("<B1-Motion>", draw)
canvas.bind("<ButtonRelease-1>", stop_drawing)

# Status bar stays at the bottom
status_label.pack(fill="x")


# Network connection
HOST = "127.0.0.1"
PORT = 5000

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client_socket.connect((HOST, PORT))
    status_label.config(text="Connected to SyncSketch server!")

except ConnectionRefusedError:
    status_label.config(text="Could not connect to server.")
    client_socket = None


receive_thread = threading.Thread(
    target=receive_drawing,
    daemon=True
    )

receive_thread.start()
root.mainloop()
