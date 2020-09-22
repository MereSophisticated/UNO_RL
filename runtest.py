import sys
import time

from tqdm import tqdm

from test import UnoTest

if len(sys.argv) != 2:
    print("Please provide path to model")
else:
    agent_wins = 0
    games = 1000
    for counter in tqdm(range(games)):
        game = UnoTest(sys.argv[1], 2)
        finished = False
        agent_random = None
        agent_tested = None
        while not finished:

            game.current_player = (game.current_player + game.turn_direction) % game.number_of_players

            if game.current_player == 0:
                agent_random = game.random_agent_move()
            else:
                agent_tested = game.agent_move()

            if agent_random == 0:
                finished = True
            elif agent_tested == 1:
                finished = True
                agent_wins += 1
    print("Games: " + str(games))
    print("Agent wins: " + str(agent_wins))
    print(agent_wins/games)

