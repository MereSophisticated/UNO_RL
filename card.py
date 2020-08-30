from termcolor import colored


class Card:
    def __init__(self, color, type, trait, action_number):
        self.color = color
        self.type = type
        self.trait = trait
        self.action_number = action_number

    def __repr__(self):
        return str(self.color) + ' - ' + str(self.type) + ' - ' + str(self.trait) \
               + ' - ' + str(self.action_number)

    @staticmethod
    def pretty_print_cards(cards, print_id):
        if print_id:
            print('0:'+colored('Draw', 'cyan'), end=' ')
        for index, card in enumerate(cards):
            if print_id:
                print(str(index+1)+':', end='')

            if card.color == 0:
                print(colored(card.trait, 'red'), end=' ')
            elif card.color == 1:
                print(colored(card.trait, 'white'), end=' ')
            elif card.color == 2:
                print(colored(card.trait, 'green'), end=' ')
            elif card.color == 3:
                print(colored(card.trait, 'blue'), end=' ')
            elif card.color == 4:
                print(colored(card.trait, 'magenta'), end=' ')
        print('\n')





