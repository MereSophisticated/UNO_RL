import numpy as np
from player import Player
from deck import Deck
from collections import Counter
from utils import COLORS


class UnoEnvironment:
    DRAW_CARD_REWARD = -5
    CARD_PLAYED_REWARD = 2
    WIN_REWARD = 50
    TRAIT_TO_INDEX = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
                      '8': 8, '9': 9, 'skip': 10, 'reverse': 11, 'draw_2': 12,
                      'wild': 13, 'draw_4': 14}
    ACTION_COUNT = 55
    STATE_SIZE = 6 * 5 * 15

    def __init__(self, number_of_players=2):
        self.deck = Deck()
        self.number_of_players = number_of_players
        self.players = [Player(self.deck.draw_cards(7)) for player in range(self.number_of_players)]
        self.played_card = None
        self.played_cards = self.reveal_top_card()
        self.top = self.played_cards[-1]
        self.turn_direction = 1
        self.current_player = 0
        self.reward = 0
        self.turn = 0
        self.done = False

    def reset(self):
        self.deck = Deck()
        self.players = [Player(self.deck.draw_cards(7)) for player in range(self.number_of_players)]
        self.played_card = None
        self.played_cards = self.reveal_top_card()
        self.top = self.played_cards[len(self.played_cards) - 1]
        self.turn_direction = 1
        self.current_player = 0
        self.reward = 0
        self.turn = 0
        self.done = False

    def get_state(self):
        state = np.zeros((6, 5, 15), dtype=int)
        player_hand = self.players[self.current_player].cards
        encoded_hand = self.encode_hand(player_hand)
        state[:4] = encoded_hand
        state[4] = self.encode_top(self.top)
        encoded_opp = self.encode_opp_hand(
            self.players[(self.current_player + self.turn_direction) % self.number_of_players].get_hand_size())
        state[5:] = encoded_opp

        return state.flatten()

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

    ''' 
        Encodes opponents hand size
        0,0,0 = 1 --> 1 card
        0,0,1 = 1 --> 2 cards
        ...
        0,0,14 = 1 --> 15 cards
        0,1,0 = 1 --> 16 cards
    '''
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

    def reveal_top_card(self):
        revealed_cards = self.deck.draw_cards(1)
        while revealed_cards[-1].type != "number":
            revealed_cards += self.deck.draw_cards(1)

        return revealed_cards

    def step(self, action):
        self.turn += 1
        player = self.players[self.current_player]
        if action != 54:
            index = [card.action_number for card in player.cards].index(action)
            self.played_card = player.cards[index]
        else:
            # Action is draw
            self.played_card = None

        if not self.played_card:
            self.draw_cards(player, 1)
            self.reward = self.DRAW_CARD_REWARD
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
            self.reward = self.CARD_PLAYED_REWARD
            self.played_cards.append(player.play_card(index))

        if len(player.cards) == 0 or self.number_of_players == 1:
            self.reward += self.WIN_REWARD
            self.done = True

        return self.get_state(), self.reward, self.done, self.turn

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

        # Only if there are no other legal actions except draw, draw_4 is legal
        if not legal_actions and draw_4_actions:
            legal_actions.append(draw_4_actions)
        legal_actions.append(54)
        return legal_actions

    def skip(self):
        self.current_player = (self.current_player + self.turn_direction) % self.number_of_players

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
    #         print("Player" + str(i) + ": ")
    #         print(-points)
    #     return points

    def draw_cards(self, player, number_of_cards_to_draw):
        # Handle empty deck
        if len(self.deck.deck) < number_of_cards_to_draw:
            self.shuffle_played_cards_into_deck()
        cards_to_draw = self.deck.draw_cards(number_of_cards_to_draw)
        player.add_cards(cards_to_draw)

    def shuffle_played_cards_into_deck(self):
        temp = [self.played_cards.pop()]
        self.deck.deck = self.played_cards
        self.played_cards = temp
        self.deck.shuffle_deck()


