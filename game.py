import numpy as np
from card import Card
from player import Player
from deck import Deck
from collections import Counter
from utils import COLORS
from keras.models import load_model


class UnoGame:
    TRAIT_TO_INDEX = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
                      '8': 8, '9': 9, 'skip': 10, 'reverse': 11, 'draw_2': 12,
                      'wild': 13, 'draw_4': 14}
    ACTION_COUNT = 55

    def __init__(self, model_path, number_of_players=2):
        self.deck = Deck()
        self.number_of_players = number_of_players
        self.players = [Player(self.deck.draw_cards(7)) for player in range(self.number_of_players)]
        self.played_card = None
        self.played_cards = self.reveal_top_card()
        self.top = self.played_cards[-1]
        self.turn_direction = 1
        self.current_player = 0
        self.done = False
        self.model = load_model(model_path)
        self.pretty_print_state()
        self.wait_for_action()

    def get_state(self):
        state = np.zeros((6, 5, 15), dtype=int)
        player_hand = self.players[self.current_player].cards
        encoded_hand = self.encode_hand(player_hand)
        state[:4] = encoded_hand
        state[4] = self.encode_top(self.top)
        encoded_opp = self.encode_opp_hand(
            self.players[(self.current_player + self.turn_direction) % self.number_of_players].get_hand_size())
        state[5:] = encoded_opp

        return state

    def state_size(self):
        return len(self.get_state())

    def encode_hand(self, hand):
        counted_hand = self.count_cards(hand)
        encoded_hand = np.zeros((4, 5, 15), dtype=int)

        for card, count in counted_hand.items():
            color = card[0]
            trait = self.TRAIT_TO_INDEX[card[2]]
            encoded_hand[count - 1][color][trait] = 1
        return encoded_hand

    def encode_opp_hand(self, hand_size):
        encoded_hand_size = np.zeros((1, 5, 15), dtype=int)
        for count in range(hand_size):
            index = 0
            if count >= 15:
                index = count / 15
                count = count % 15
            encoded_hand_size[0][int(index)][int(count)] = 1
        return encoded_hand_size

    def encode_top(self, top):
        encoded_top = np.zeros((1, 5, 15), dtype=int)
        encoded_top[0][top.color][self.TRAIT_TO_INDEX[top.trait]] = 1
        return encoded_top

    def count_cards(self, hand):
        return Counter((card.color, card.type, card.trait, card.action_number) for card in hand)

    def wait_for_action(self):
        player = self.players[self.current_player]

        illegal_input = True
        while illegal_input:
            action_input = int(input("Get action:"))
            if 0 <= action_input <= player.get_hand_size():
                if action_input == 0:
                    action = 54
                    self.played_card = None
                    illegal_input = False
                else:
                    self.played_card = player.cards[action_input - 1]
                    action = player.cards[action_input - 1].action_number
                    if action in self.get_legal_actions():
                        illegal_input = False
                    else:
                        print("You can't do that")
            else:
                print("You can't do that")
        self.step(action)

    def reveal_top_card(self):
        revealed_cards = self.deck.draw_cards(1)
        while revealed_cards[-1].type != "number":
            revealed_cards += self.deck.draw_cards(1)

        return revealed_cards

    def step(self, action):
        player = self.players[self.current_player]
        if action != 54:
            index = [card.action_number for card in player.cards].index(action)
            self.played_card = player.cards[index]
        else:
            self.played_card = None

        if not self.played_card:
            self.draw_cards(player, 1)
        else:
            if self.played_card.trait == "skip":
                self.skip()
            elif self.played_card.trait == "reverse":
                self.reverse_turn()
            elif self.played_card.trait == "draw_2":
                self.draw_cards(self.players[(self.current_player + self.turn_direction) % self.number_of_players], 2)
                self.skip()
            elif self.played_card.trait == "wild":
                self.played_card.color = np.random.randint(COLORS)
            elif self.played_card.trait == "draw_4":
                self.draw_cards(self.players[(self.current_player + self.turn_direction) % self.number_of_players], 4)
                self.played_card.color = np.random.randint(COLORS)
                self.skip()
            self.played_cards.append(player.play_card(index))

        if len(player.cards) == 0:
            self.done = True
            if self.current_player == 0:
                print("Player wins!")
            else:
                print("AI wins!")
        else:
            self.next_turn()

    def get_legal_actions(self):
        player = self.players[self.current_player]
        self.top = self.played_cards[-1]
        legal_actions = []
        draw_4_actions = []
        if self.top.type == "wild":
            for card in player.cards:
                if card.type == "wild":
                    if card.trait == "draw_4":
                        draw_4_actions = card.action_number
                    else:
                        legal_actions.append(card.action_number)
                if card.color == self.top.color:
                    legal_actions.append(card.action_number)

        else:
            for card in player.cards:
                if card.type == "wild":
                    if card.trait == "draw_4":
                        draw_4_actions = card.action_number
                    else:
                        legal_actions.append(card.action_number)
                if card.color == self.top.color or card.trait == self.top.trait:
                    legal_actions.append(card.action_number)

        # Only if there are no other legal actions, draw 4 can be played
        if not legal_actions and draw_4_actions:
            legal_actions.append(draw_4_actions)
        legal_actions.append(54)
        return legal_actions

    def skip(self):
        self.current_player = (self.current_player + self.turn_direction) % self.number_of_players

    def next_turn(self):
        self.current_player = (self.current_player + self.turn_direction) % self.number_of_players

        if self.current_player == 0:
            self.pretty_print_state()
            self.wait_for_action()
        else:
            self.agent_move()

    def agent_move(self):
        state = self.get_state().flatten()
        values = self.model.predict(np.array(state).reshape(-1, *state.shape))[0]
        legal_actions = self.get_legal_actions()
        max_index = 0
        for index, action in enumerate(legal_actions):
            if values[action] > values[max_index]:
                max_index = index
        action = legal_actions[max_index]
        self.step(action)

    def reverse_turn(self):
        self.turn_direction *= -1
        if self.number_of_players == 2:
            self.skip()

    # def calculate_points(self):
    #     points = []
    #     for i, player in enumerate(self.players):
    #         points_n = 0
    #         for card in player.cards:
    #             if card.type == "number":
    #                 points_n += card.trait
    #             elif card.type == "action":
    #                 points_n += 20
    #             elif card.type == "wild":
    #                 points_n += 50
    #         points.append(points_n)
    #     return points

    def draw_cards(self, player, number_of_cards_to_draw):
        if len(self.deck.deck) < number_of_cards_to_draw:
            self.shuffle_played_cards_into_deck()
        cards_to_draw = self.deck.draw_cards(number_of_cards_to_draw)
        player.add_cards(cards_to_draw)

    def shuffle_played_cards_into_deck(self):
        temp = [self.played_cards.pop()]
        self.deck.deck = self.played_cards
        self.played_cards = temp
        self.deck.shuffle_deck()

    def pretty_print_state(self):
        print("-------------------------------------------------------------------------------------------------------")
        print("Revealed card:")
        Card.pretty_print_cards(self.played_cards[len(self.played_cards) - 1:], False)

        for player in range(self.number_of_players):
            if player == 0:
                if player == self.current_player:
                    print("ACTIVE-", end='')
                print("My hand:")
                self.players[player].print_hand()
            else:
                if player == self.current_player:
                    print("ACTIVE-", end='')
                print("Their hand:")
                self.players[player].print_hand()
        print("-------------------------------------------------------------------------------------------------------")
