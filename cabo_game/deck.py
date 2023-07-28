# deck.py

import random

# Define card ranks
CARD_RANKS = ['K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2', 'A']
SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
DECK = [rank + ' ' + suit for rank in CARD_RANKS for suit in SUITS]


def shuffle_deck():
    random.shuffle(DECK)


def deal_hand(num_cards):
    hand = []
    for _ in range(num_cards):
        card = DECK.pop()
        hand.append(card)
    return hand
