import threading
import os
import random
import numpy as np
import utils
from collections import deque
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam
from tqdm import tqdm
from environment import UnoEnvironment


class DQNAgent:

    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.initialized = False
        self.training = True
        self.replay_memory_size = 10000
        self.replay_memory = deque(maxlen=self.replay_memory_size)
        self.batch_size = 512
        self.model_update_frequency = 50
        self.gamma = 0.7  # discount factor
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.999999
        self.learning_rate = 0.001
        self.model = self.build_model()
        self.target_model = self.build_model()
        self.target_model.set_weights(self.model.get_weights())

    def build_model(self):
        model = Sequential()
        model.add(Dense(64, input_shape=(6 * 5 * 15,), activation='relu'))
        model.add(Dense(64, activation='relu'))
        model.add(Dense(units=64, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mse',
                      optimizer=Adam(lr=self.learning_rate))
        return model

    def add_transition_to_memory(self, transition):
        self.replay_memory.append(transition)

    def predict(self, state):
        return self.model.predict(np.array(state).reshape(-1, *state.shape))[0]

    def train(self):
        while len(self.replay_memory) < self.batch_size:
            continue
        for counter in tqdm(range(1, 1001)):
            mini_batch = np.array(random.sample(self.replay_memory, self.batch_size), dtype=object)

            states = np.array(list(mini_batch[:, 0]))

            q_values = self.model.predict(states)

            max_future_q = np.max(self.model.predict(np.array(list(mini_batch[:, 3]))), axis=1)

            for i in range(len(mini_batch)):
                # transition: state, action, reward, new_state, done
                action, reward, done = mini_batch[i, 1], mini_batch[i, 2], mini_batch[i, 4]
                q_values[i, action] = reward
                if not done:
                    q_values[i, action] += self.gamma * max_future_q[i]

            self.target_model.fit(x=states, y=q_values, batch_size=self.batch_size, verbose=0)

            if counter % self.model_update_frequency == 0:
                self.model.set_weights(self.target_model.get_weights())
                if not self.initialized:
                    self.initialized = True

        self.training = False
        print("Saving")
        folder = f'models/{utils.get_timestamp()}'
        if not os.path.exists(folder):
            os.makedirs(folder)
        self.model.save(f'{folder}/model.h5')


def run(agent):
    env = UnoEnvironment(2)

    while agent.training:
        done = False
        state = None
        rewards = []

        while not done:
            legal_actions = env.get_legal_actions()
            if state is None or np.random.sample() < agent.epsilon or not agent.initialized:
                # Choose a random legal action
                action = np.random.choice(legal_actions, 1)
            else:
                # Choose a legal action from the policy
                max_index = 0
                values = agent.predict(state)
                for index, action in enumerate(legal_actions):
                    if values[action] > values[max_index]:
                        max_index = index
                action = legal_actions[max_index]

            new_state, reward, done, _ = env.step(action)
            rewards.append(reward)

            if state is not None:
                agent.add_transition_to_memory((state, action, reward, new_state, done))
            state = new_state

            if agent.initialized:
                if agent.epsilon > agent.epsilon_min:
                    agent.epsilon *= agent.epsilon_decay
        env.reset()


if __name__ == '__main__':
    agent = DQNAgent(UnoEnvironment.STATE_SIZE, UnoEnvironment.ACTION_COUNT)

    for thread in range(3):
        threading.Thread(target=run, args=(agent,), daemon=True).start()
    agent.train()
