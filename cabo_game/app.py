# app.py (updated)

from flask import Flask, render_template, jsonify
from deck import shuffle_deck, deal_hand

app = Flask(__name__)

# Global variables to keep track of the game state
players = []
pile = []


@app.route('/')
def start_game():
    return render_template('start_screen.html', players=players)


@app.route('/deal', methods=['POST'])
def deal():
    try:
        shuffle_deck()
        for _ in range(4):
            players.append(deal_hand(4))
        print(jsonify(players))
        print(players)

        return jsonify(players)
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
