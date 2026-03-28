"""
Traffic light agent – manages traffic light state switching.
Direct port of TrafficLightAgent.cs.
"""

import utils
from agent_framework import TurnBasedAgent, Message


class TrafficLightAgent(TurnBasedAgent):

    def __init__(self, tl_id: int, pos_x: int, pos_y: int,
                 no_turns: int, initial_state: utils.TrafficLightState):
        super().__init__()
        self._id = tl_id
        self._x = pos_x
        self._y = pos_y
        self._no_turns = no_turns
        self._state = initial_state
        self._current_no_turns = 0

    def setup(self):
        print(f"Starting {self.name} with state {self._state.value}")
        self.send("intersection",
                  utils.str_msg("trafficLight", self._x, self._y, self._state.value))

    def act(self, messages: list[Message]):
        for message in messages:
            print(f"\t[{message.sender} -> {self.name}]: {message.content}")

            action, parameters = utils.parse_message_matrix(
                message.content, self._x, self._y)

            if action == "change":
                self._parse_state(parameters)

                if self._current_no_turns == self._no_turns:
                    self._switch_state()
                    self._current_no_turns = 0
                    self.send("intersection",
                              utils.str_msg("changeLight", self._x, self._y,
                                            self._state.value))
                else:
                    self.send("intersection",
                              utils.str_msg("noChangeLight", self._x, self._y))

                self._current_no_turns += 1

    def _switch_state(self):
        if self._state == utils.TrafficLightState.Green:
            self._state = utils.TrafficLightState.Red
        else:
            self._state = utils.TrafficLightState.Green

    def _parse_state(self, values):
        """Placeholder for adaptive traffic light algorithms (not implemented in original)."""
        pass
