import pygame
import json
import pickle
import random
import socket
import threading
import signal
import sys
server_socket = None  # Declare server_socket as a global variable
BUFFER_SIZE = 4096

# Constants
CARD_RANKS = ['K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2', 'A']
SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
DECK = [rank + ' ' + suit for rank in CARD_RANKS for suit in SUITS]
CARD_WIDTH, CARD_HEIGHT = 100, 150

# Initialize Pygame
pygame.init()
window_size = (800, 800)
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption('Cabo Game')

# Load font for card text
font = pygame.font.Font(None, 30)

def shuffle_deck():
    random.shuffle(DECK)

def deal_hand(num_cards):
    hand = []
    for _ in range(num_cards):
        card = DECK.pop()
        hand.append(card)
    return hand

def draw_card(x, y, rank=None, suit=None, face_down=True):
    # Draw a card with a rectangle for the card background and text for rank and suit
    card_rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
    pygame.draw.rect(screen, (255, 255, 255), card_rect)
    pygame.draw.rect(screen, (0, 0, 0), card_rect, 2)

    if face_down:
        pygame.draw.rect(screen, (0, 0, 0), card_rect)
    else:
        if rank is not None and suit is not None:
            rank_text = font.render(rank, True, (0, 0, 0))
            suit_text = font.render(suit, True, (0, 0, 0))
            rank_rect = rank_text.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT // 3))
            suit_rect = suit_text.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2))
            screen.blit(rank_text, rank_rect)
            screen.blit(suit_text, suit_rect)


def draw_border(x, y, width, height, thickness):
    pygame.draw.rect(screen, (50, 50, 50), (x, y, width, height), thickness)

def draw_deck(deck_count):
    x_offset = 350
    y_offset = 500
    card_gap = 0.5  # Angle gap between cards in radians
    card_angle = -15  # Initial angle of the cards in degrees
    card_thickness = 1

    for i in range(deck_count):
        draw_card(x_offset + i * card_thickness, y_offset - i * card_thickness, "Deck", "Back", face_down=True)
        draw_border(x_offset + i * card_thickness, y_offset - i * card_thickness, CARD_WIDTH, CARD_HEIGHT, card_thickness)

def draw_game_screen(players, player_hands, player_turn, revealed_status, cards_revealed, deck_count):
    screen.fill((255, 255, 255))

    # Draw player turn and instructions at the top middle
    turn_text = font.render(f"{players[player_turn]}'s Turn", True, (0, 0, 0))
    instructions_text = font.render("Click on your facedown cards to reveal them.", True, (0, 0, 0))
    turn_text_rect = turn_text.get_rect(center=(window_size[0] // 2, 50))
    instructions_text_rect = instructions_text.get_rect(center=(window_size[0] // 2, 90))
    screen.blit(turn_text, turn_text_rect)
    screen.blit(instructions_text, instructions_text_rect)

    # Draw deck (stack of cards) under the info text
    draw_deck(deck_count)

    # Draw player hands
    for i, hand in enumerate(player_hands):
        x_offset = 100 + i * 400
        y_offset = 200
        for j, card in enumerate(hand):
            if revealed_status[i][j]:
                draw_card(x_offset + (j % 2) * 110, y_offset + (j // 2) * 180, *card.split(), face_down=False)
            else:
                draw_card(x_offset + (j % 2) * 110, y_offset + (j // 2) * 180, face_down=True)
            draw_border(x_offset + (j % 2) * 110, y_offset + (j // 2) * 180, CARD_WIDTH, CARD_HEIGHT, 2)

    # Draw end turn button at the bottom in the middle
    end_turn_button = pygame.Rect(window_size[0] // 2 - 100, window_size[1] - 100, 200, 50)
    pygame.draw.rect(screen, (200, 200, 200), end_turn_button)
    end_turn_text = font.render("End Turn", True, (0, 0, 0))
    end_turn_text_rect = end_turn_text.get_rect(center=end_turn_button.center)
    screen.blit(end_turn_text, end_turn_text_rect)


def handle_events(players, player_hands, player_turn, revealed_status, cards_revealed):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, player_turn, cards_revealed

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            for i, hand in enumerate(player_hands):
                x_offset = 100 + i * 400
                y_offset = 200
                for j, card in enumerate(hand):
                    card_rect = pygame.Rect(x_offset + (j % 2) * 110, y_offset + (j // 2) * 180, CARD_WIDTH, CARD_HEIGHT)
                    if card_rect.collidepoint(mouse_x, mouse_y) and (player_turn == i or revealed_status[i][j]):
                        # Reveal the card if it's the current player's turn or already revealed
                        if not revealed_status[i][j] and cards_revealed < 2:
                            revealed_status[i][j] = True
                            cards_revealed += 1

            end_turn_button = pygame.Rect(window_size[0] // 2 - 100, window_size[1] - 100, 200, 50)
            if cards_revealed >= 2 and end_turn_button.collidepoint(mouse_x, mouse_y) and pygame.mouse.get_pressed()[0]:
                # Reset for the next player's turn
                player_turn = (player_turn + 1) % len(players)
                cards_revealed = 0
                for hand in revealed_status:
                    for i in range(len(hand)):
                        hand[i] = False

    return True, player_turn, cards_revealed


def send_initial_data(client_socket, players, player_hands, revealed_status, deck_count,player_turn):
    print("send_initial_data")
    data = {
        "players": players,
        "player_hands": player_hands,
        "revealed_status": revealed_status,
        "deck_count": deck_count,
        "player_turn":player_turn
    }
    print(data)
    serialized_data = pickle.dumps(data)
    # client_socket.send(serialized_data)
    client_socket.sendall(serialized_data)
    return

def handle_client(client_socket, players, player_hands, revealed_status, deck_count,player_turn,client_sockets):
    # Wait for the "Ready" message from the client before proceeding
    ready_message = client_socket.recv(BUFFER_SIZE).decode()
    print(ready_message)
    if ready_message == "Ready to send initial data":
        print("sending   _initial_data")
        send_initial_data(client_socket, players, player_hands, revealed_status, deck_count,player_turn)

    while True:
        try:
            # Receive data in a loop until all data is received
            serialized_request = b""
            while True:
                chunk = client_socket.recv(4096)  # Increase buffer size if needed
                if not chunk:
                    break
                serialized_request += chunk

            if not serialized_request:
                break
            print(serialized_request)

            # request = pickle.loads(serialized_request)
            # Process client's request (game logic)
            # For example, update the game state (player_hands, revealed_status) based on the client's action.


            # Receive data from the server
            # serialized_data = client_socket.recv(BUFFER_SIZE)
            # if not serialized_data:
            #     break

            # data = pickle.loads(serialized_data)
            # # Check if the received data contains a test message
            # if "test_message" in data:
            #     print(f"Received message from server: {data['test_message']}")

            # Send the updated game state back to all clients
            updated_data = {
                "players": players,
                "player_hands": player_hands,
                "revealed_status": revealed_status,
                "deck_count": deck_count,
                "player_turn": player_turn  # Include the player_turn in the updated_data

            }
            serialized_updated_data = pickle.dumps(updated_data)
            # Broadcast the updated game state to all connected clients
            for client_socket in client_sockets:
                client_socket.send(serialized_updated_data)        
        except Exception as e:
            print(f"Error handling client: {e}")
            break

    client_socket.close()

def game_server(num_players, players, client_sockets):
    # Initialize the player hands for each connected player
    player_hands = []
    for _ in range(num_players):
        player_hands.append(deal_hand(4))

    for client_socket, hand in zip(client_sockets, player_hands):
        hand_str = ",".join(hand)
        client_socket.send(hand_str.encode())

    # Initialize player turn and revealed status for each card in each player's hand
    player_turn = 0
    revealed_status = [[False] * len(hand) for hand in player_hands]
    cards_revealed = 0

    # Initialize the number of cards in the deck
    deck_count = len(DECK) - num_players * 4

    # Call handle_client function for each connected client
    players, player_hands, deck_count = setup_game(num_players)
    threads = []
    for client_socket in client_sockets:
        thread = threading.Thread(target=handle_client, args=(client_socket, players, player_hands, revealed_status, deck_count, player_turn, client_sockets))
        thread.start()
        threads.append(thread)

    # New function to send a message to a specific client
    def send_message(client_socket, message):
        try:
            serialized_message = pickle.dumps(message)
            client_socket.send(serialized_message)
        except Exception as e:
            print(f"Error sending message: {e}")

    # Game loop
    running = True
    while running:
        try:
            # Receive data from each connected client and update the game state accordingly
            for i, client_socket in enumerate(client_sockets):
                serialized_data = client_socket.recv(BUFFER_SIZE)
                if not serialized_data:
                    break
                
                print("game_server loads data")
                data = pickle.loads(serialized_data)
                print(data)
                # Process client's data (e.g., update revealed_status or any other game logic)
                
                # Update the player_turn for the next turn
                player_turn = (player_turn + 1) % num_players               
                # Send the updated game state back to the client
                updated_data = {
                    "players": players,
                    "player_hands": player_hands,
                    "revealed_status": revealed_status,
                    "deck_count": deck_count,
                    "player_turn": player_turn  # Include the player_turn in the updated_data

                }
                serialized_updated_data = pickle.dumps(updated_data)
                client_socket.send(serialized_updated_data)

            # Check if the game should continue or end based on game logic
            # You may also implement a condition to terminate the game loop if needed.
            # Send a test message to the first client (you can modify this as needed)
            if len(client_sockets) >= 1:
                send_message(client_sockets[0], "This is a test message!")

            draw_game_screen(players, player_hands, player_turn, revealed_status, cards_revealed, deck_count)
            pygame.display.flip()

        except Exception as e:
            print(f"Error handling client: {e}")
            break

def recvall(sock, length):
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            break
        data += chunk
    return data

def receive_initial_data(client_socket):
    print("receive_initial_data to server")

    serialized_data = b""
    # while True:
    #     chunk = client_socket.recv(4096)
    #     if not chunk:
    #         break
    #     serialized_data += chunk
    chunk = client_socket.recv(BUFFER_SIZE)
    serialized_data += chunk

    # Receive all data until there's nothing left to receive
    # data_bytes = recvall(client_socket, BUFFER_SIZE)  # Increase buffer size if needed
    # try:
    #     data = pickle.loads(data_bytes)
    #     print(data)
    #     # return data 
    #     return data["players"], data["player_hands"], data["revealed_status"], data["deck_count"]
    # except Exception as e:
    #     print("Error deserializing data:", e)
    #     return None, None, None, None

    print("pickle to server")
    print(serialized_data)
    data = pickle.loads(serialized_data)
    print(data)
    return data["players"], data["player_hands"], data["revealed_status"], data["deck_count"]


# Function to connect to the server
def connect_to_server(player_turn,cards_revealed):
    print("Connect to server")
    global server_socket  # Make server_socket a global variable

    host = '127.0.0.1' #input("Enter the server IP address: ")
    port = 12345  # Port number (same as the server's port)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    # After connecting to the server, send a message to indicate readiness
    ready_message = "Ready to send initial data"
    client_socket.send(ready_message.encode())

    # Receive the player's initial hand from the server
    # hand_str = client_socket.recv(1024).decode()
    # Receive the player's initial hand from the server
    # hand_bytes = recvall(client_socket, 1024)
    # player_hand = pickle.loads(hand_bytes)
    # print("player_hand:")
    # print(player_hand)

    # Receive the initial data (game state) from the server
    # Receive the initial data (game state) from the server
    # data_bytes = recvall(client_socket, BUFFER_SIZE)  # Increase buffer size if needed
    # print(data_bytes)
    # players, player_hands, revealed_status, deck_count = pickle.loads(data_bytes)

    players, player_hands, revealed_status, deck_count = receive_initial_data(client_socket)
    print(players)
    # Game loop for the client
    running = True
    while running:
        try:
            # ... (Existing code) ...
            running, player_turn, cards_revealed = handle_events(players, player_hands, player_turn, revealed_status, cards_revealed)
            draw_game_screen(players, player_hands, player_turn, revealed_status, cards_revealed, deck_count)
            pygame.display.flip()

            # Send the player's action to the server (e.g., which card to reveal)
            # print("before action")
            action = {"player_turn": player_turn, "revealed_status": revealed_status}  # Your action data
            serialized_action = pickle.dumps(action)
            client_socket.send(serialized_action)

            # Receive the updated game state from the server
            serialized_updated_data = client_socket.recv(BUFFER_SIZE)
            # print("serialized_updated_data ")
            # print(serialized_updated_data)

            # updated_data = pickle.loads(serialized_updated_data)
            # print("after pickle serialized_updated_data ")

            # players = updated_data["players"]
            # player_hands = updated_data["player_hands"]
            # revealed_status = updated_data["revealed_status"]
            # deck_count = updated_data["deck_count"]
            # # Update the player_turn value based on the updated game state
            # player_turn = updated_data["player_turn"]

            # Example of sending a test message to one of the players
            # if player_turn == 0 and not revealed_status[0][0]:  # Assuming player 0 has not revealed their first card yet
            test_message = "This is a test message from the server!"
            client_socket.send(test_message.encode())
        except Exception as e:
            print(f"Error connecting to server: {e}")
            break
    client_socket.close()



def setup_game(num_players):
    players = [f"Player {i+1}" for i in range(num_players)]
    player_hands = []

    shuffle_deck()
    for _ in range(num_players):
        player_hands.append(deal_hand(4))

    deck_count = len(DECK) - num_players * 4

    return players, player_hands, deck_count

def lobby(num_players, server_socket,revealed_status,player_turn):
    print("Waiting for players to join...")
    client_sockets = []
    while len(client_sockets) < num_players:
        client_socket, _ = server_socket.accept()
        client_sockets.append(client_socket)
        print(f"Player {len(client_sockets)} connected.")
    
    # Call handle_client function for each connected client
    players, player_hands, deck_count = setup_game(num_players)
    
    # Send initial data to all clients before starting the game loop
    for client_socket in client_sockets:
        send_initial_data(client_socket, players, player_hands, revealed_status, deck_count,player_turn)

    print("All players connected. Starting the game.")
    
    threads = []
    for client_socket in client_sockets:
        thread = threading.Thread(target=handle_client, args=(client_socket, players, player_hands, revealed_status, deck_count, player_turn, client_sockets))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish (when all clients are disconnected)
    for thread in threads:
        thread.join()

    print("All clients disconnected. Ending the game.")
    server_socket.close()
    sys.exit(0)


def main():
    global server_socket  # Declare server_socket as a global variable

    print("Welcome to Tamaloo!")
    choice = input("Press 'c' to connect to a game or 's' to create a server: ")
    player_turn = 0
    cards_revealed = 0

    if choice.lower() == "c":
        # Connect to the server
        connect_to_server(player_turn,cards_revealed)
    elif choice.lower() == "s":
        # Set up the server and accept client connections
        num_players = int(input("Enter the number of players: "))
        players, player_hands, deck_count = setup_game(num_players)

        # Server setup
        host = "127.0.0.1"  # Server IP address
        port = 12345       # Port number (choose any available port)

        # Set up the signal handler to catch SIGINT (Ctrl+C)
        signal.signal(signal.SIGINT, signal_handler)

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(num_players)  # Set the maximum number of players allowed

        print(f"Server listening on {host}:{port}")
        # Initialize player turn and revealed status for each card in each player's hand
        revealed_status = [[False] * len(hand) for hand in player_hands]
        # Wait for players to join the lobby and get the updated client_sockets list
        client_sockets = lobby(num_players, server_socket,revealed_status,player_turn)

        # Broadcast each player's hand to all clients
        for client_socket, hand in zip(client_sockets, player_hands):
            hand_str = ",".join(hand)
            client_socket.send(hand_str.encode())

  

        # Game loop
        running = True
        while running:
            running, player_turn, cards_revealed = game_server(num_players, players, client_sockets)
            # The rest of the code in the main function remains unchanged.
            draw_game_screen(players, player_hands, player_turn, revealed_status, cards_revealed, deck_count)
            pygame.display.flip()

        pygame.quit()



    


def signal_handler(sig, frame):
    print("\nServer terminated by user.")
    if server_socket:
        server_socket.close()
    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()


# def main():
#     # Game setup
#     num_players = int(input("Enter the number of players: "))
#     players = [f"Player {i+1}" for i in range(num_players)]
#     player_hands = []

#     shuffle_deck()
#     for _ in range(num_players):
#         player_hands.append(deal_hand(4))

#     # Initialize player turn and revealed status for each card in each player's hand
#     player_turn = 0
#     revealed_status = [[False] * len(hand) for hand in player_hands]
#     cards_revealed = 0

#     # Initialize the number of cards in the deck
#     deck_count = len(DECK) - num_players * 4

#     # Game loop
#     running = True
#     while running:
#         running, player_turn, cards_revealed = handle_events(players, player_hands, player_turn, revealed_status, cards_revealed)
#         draw_game_screen(players, player_hands, player_turn, revealed_status, cards_revealed, deck_count)
#         pygame.display.flip()

#     pygame.quit()