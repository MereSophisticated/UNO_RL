from card import Card
from random import shuffle
from utils import COLORS


class Deck:

    def __init__(self):
        self.deck = self.generate_deck()
        self.shuffle_deck()

    @staticmethod
    def generate_deck():
        # Create 0 - 9  for each color
        cards = [Card(color, "number", str(number), number+13*color) for color in range(COLORS) for number in range(10)]

        # Create 1 - 9 for each color
        cards += [Card(color, "number", str(number+1), number+1 + 13 * color) for color in range(COLORS) for number in range(9)]

        # Create skip for each color
        cards += [Card(color, "action", "skip", 10 + 13 * color) for color in range(COLORS)]
        cards += [Card(color, "action", "skip", 10 + 13 * color) for color in range(COLORS)]

        # Create reverse for each color
        cards += [Card(color, "action", "reverse", 11 + 13 * color) for color in range(COLORS)]
        cards += [Card(color, "action", "reverse", 11 + 13 * color) for color in range(COLORS)]

        # Create draw_2 for each color
        cards += [Card(color, "action", "draw_2", 12 + 13 * color) for color in range(COLORS)]
        cards += [Card(color, "action", "draw_2", 12 + 13 * color) for color in range(COLORS)]

        # Create wild cards
        cards += [Card(4, "wild", "wild", 52) for color in range(COLORS)]

        # Create draw_4 cards
        cards += [Card(4, "wild", "draw_4", 53) for color in range(COLORS)]

        return cards

    def shuffle_deck(self):
        shuffle(self.deck)

    def draw_cards(self, number=7):
        drawn_cards = self.deck[:number]
        del self.deck[:number]
        return drawn_cards

    def pretty_print_deck(self):
        Card.pretty_print_cards(self.cards, False)

