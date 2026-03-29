"""
Intersection agent – central coordinator for the traffic simulation.
Direct port of IntersectionAgent.cs.
"""

import threading
import time
import utils
from agent_framework import TurnBasedAgent, Message
from intersection_gui import IntersectionGUI


class IntersectionAgent(TurnBasedAgent):

    def __init__(self, total_cars: int = 0):
        super().__init__()
        self.car_positions: dict[str, list[str]] = {}
        self.traffic_light_positions: dict[str, list[str]] = {}
        self._traffic_light_states: list[list[utils.TrafficLightState]] = []
        self._no_cars_per_cell: list[list[int]] = []
        self._total_cars = total_cars
        self._finished_cars = 0
        self._form_gui = IntersectionGUI()

        # Start GUI in a separate thread
        self._gui_thread = threading.Thread(target=self._gui_thread_func, daemon=True)
        self._gui_thread.start()

    def _gui_thread_func(self):
        self._form_gui.set_owner(self)
        self._form_gui.create_window()

    def setup(self):
        print(f"Starting {self.name}")
        time.sleep(1)

        self._no_cars_per_cell = [[0] * utils.SIZE for _ in range(utils.SIZE)]
        self._traffic_light_states = [
            [utils.TrafficLightState.Unavailable] * utils.SIZE for _ in range(utils.SIZE)
        ]

        for i in range(utils.SIZE):
            for j in range(utils.SIZE):
                if i % 2 != 0 and j % 2 != 0:
                    self._no_cars_per_cell[i][j] = -1

    def act(self, messages: list[Message]):
        print("New turn")
        for message in messages:
            print(f"\t[{message.sender} -> {self.name}]: {message.content}")

            action, parameters = utils.parse_message_list(message.content)

            if action == "position":
                self._handle_position(message.sender, parameters)
            elif action == "trafficLight":
                self._handle_traffic_light_position(message.sender, parameters)
            elif action == "changeLight":
                self._handle_change_light(message.sender, parameters)
            elif action == "noChangeLight":
                self._handle_no_change_light(message.sender, parameters)
            elif action == "change":
                self._handle_change(message.sender, parameters)
            elif action == "finish":
                self._remove_car(message.sender, parameters)

            self._form_gui.update_gui()

    def _handle_traffic_light_position(self, sender: str, position: list[str]):
        self.traffic_light_positions[sender] = position

        x = int(position[0])
        y = int(position[1])
        state = utils.TrafficLightState(position[2])

        self._traffic_light_states[x][y] = state

        content = utils.build_message(self._no_cars_per_cell, "change", x, y)
        self.send(sender, content)

    def _handle_change_light(self, sender: str, position: list[str]):
        self.traffic_light_positions[sender] = position

        x = int(position[0])
        y = int(position[1])
        state = utils.TrafficLightState(position[2])

        self._traffic_light_states[x][y] = state

        content = utils.build_message(self._no_cars_per_cell, "change", x, y)
        self.send(sender, content)

    def _handle_no_change_light(self, sender: str, position: list[str]):
        x = int(position[0])
        y = int(position[1])

        content = utils.build_message(self._no_cars_per_cell, "change", x, y)
        self.send(sender, content)

    def _handle_position(self, sender: str, position: list[str]):
        left_cell = -1
        up_cell = 0
        right_cell = -1
        left_cell_light = utils.TrafficLightState.Green
        up_cell_light = utils.TrafficLightState.Green
        right_cell_light = utils.TrafficLightState.Green

        self.car_positions[sender] = position
        self.send(sender, utils.str_msg(
            "move", left_cell, up_cell, right_cell,
            left_cell_light.value, up_cell_light.value, right_cell_light.value
        ))

    def _remove_car(self, sender: str, position: list[str]):
        x = int(position[0])
        y = int(position[1])

        if sender in self.car_positions:
            del self.car_positions[sender]

        self._no_cars_per_cell[x][y] -= 1
        self._finished_cars += 1
        print(f"\t[{self.name}]: {sender} finished ({self._finished_cars}/{self._total_cars})")

        if self._finished_cars >= self._total_cars:
            print(f"\n*** All {self._total_cars} cars have arrived! Simulation complete. ***")
            self._form_gui.update_gui()  # final GUI update
            if self._environment:
                self._environment.stop()

    def _handle_change(self, sender: str, position: list[str]):
        # Get old and new positions
        old_x = int(self.car_positions[sender][0])
        old_y = int(self.car_positions[sender][1])
        new_x = int(position[0])
        new_y = int(position[1])

        light_for_stop = utils.TrafficLightState.Red

        if new_y - old_y != 0:          # Traffic light is up
            light_for_stop = utils.TrafficLightState.Red
        elif new_x - old_x != 0:        # Traffic light is left or right
            light_for_stop = utils.TrafficLightState.Green

        if self._traffic_light_states[new_x][new_y] == light_for_stop:
            # Traffic light stop
            self.send(sender, "block")
        elif self._no_cars_per_cell[new_x][new_y] < utils.MAX_NO_CARS_PER_CELL:
            # Go to next position
            self._no_cars_per_cell[new_x][new_y] += 1
            if old_y != utils.SIZE:
                self._no_cars_per_cell[old_x][old_y] -= 1

            left_cell = -1
            up_cell = -1
            right_cell = -1
            left_cell_light = utils.TrafficLightState.Unavailable
            up_cell_light = utils.TrafficLightState.Unavailable
            right_cell_light = utils.TrafficLightState.Unavailable

            if new_x - 2 > 0 and self._no_cars_per_cell[new_x - 1][new_y] != -1:
                left_cell = self._no_cars_per_cell[new_x - 1][new_y]
                left_cell_light = self._traffic_light_states[new_x - 2][new_y]

            if new_y - 2 > 0 and self._no_cars_per_cell[new_x][new_y - 1] != -1:
                up_cell = self._no_cars_per_cell[new_x][new_y - 1]
                up_cell_light = self._traffic_light_states[new_x][new_y - 2]

            if new_x + 2 < utils.SIZE and self._no_cars_per_cell[new_x + 1][new_y] != -1:
                right_cell = self._no_cars_per_cell[new_x + 1][new_y]
                right_cell_light = self._traffic_light_states[new_x + 2][new_y]

            self.car_positions[sender] = position
            self.send(sender, utils.str_msg(
                "move", left_cell, up_cell, right_cell,
                left_cell_light.value, up_cell_light.value, right_cell_light.value
            ))
        else:
            # Too many cars
            self.send(sender, "block")
