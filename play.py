import sys
from game import UnoGame

if len(sys.argv) != 2:
    print("Please provide path to model")
else:
    game = UnoGame(sys.argv[1], 2)
