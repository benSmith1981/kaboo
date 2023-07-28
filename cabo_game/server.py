import socket
import threading
import signal
import sys

server_socket = None  # Declare server_socket as a global variable

def handle_client(client_socket):

    # Placeholder function to handle client requests
    while True:
        request = client_socket.recv(1024).decode()
        if not request:
            client_socket.close()
            break

        # Process client's request (game logic)
        response = f"Server received: {request}"
        client_socket.send(response.encode())

    client_socket.close()

def signal_handler(sig, frame):
    # Perform cleanup tasks here (e.g., close the server socket)
    print("\nServer terminated by user.")
    server_socket.close()
    sys.exit(0)


def start_server():
    global server_socket  # Make server_socket a global variable
    host = "127.0.0.1"  # Server IP address
    port = 12345       # Port number (choose any available port)

    # Set up the signal handler to catch SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)

    print(f"Server listening on {host}:{port}")

    lobby = []
    while True:
        client_socket, client_address = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()
        print(f"Connection from {client_address}")

        # Add client to the lobby
        lobby.append(client_socket)

        # Check if the game should start
        if len(lobby) >= 2:
            start_game_button = input("Press 's' to start the game: ")
            if start_game_button.lower() == "s":
                break

    # Start the game with all players in the lobby
    for client_socket in lobby:
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

    # Wait for all client threads to finish before exiting
    for client_handler in threading.enumerate():
        if client_handler != threading.current_thread():
            client_handler.join()


def connect_to_server():
    host = input("Enter the server IP address: ")
    port = 12345  # Port number (same as the server's port)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    while True:
        # Get input from the player (e.g., actions in the game)
        message = input("Enter your move: ")
        client_socket.send(message.encode())

        response = client_socket.recv(1024).decode()
        print(response)

    client_socket.close()

def main():
    print("Welcome to Tamaloo!")
    choice = input("Press 'c' to connect to a game or 's' to create a server: ")

    if choice.lower() == "c":
        connect_to_server()
    elif choice.lower() == "s":
        start_server()

if __name__ == "__main__":
    main()