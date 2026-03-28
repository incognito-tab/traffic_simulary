"""
Car agent – handles car movement through the traffic grid.
Direct port of CarAgent.cs.
"""

import utils
from agent_framework import TurnBasedAgent, Message


class CarAgent(TurnBasedAgent):

    def __init__(self, car_id: int, skipped_turns: int, start_pos: int,
                 car_priority: utils.CarPriorityState):
        super().__init__()
        self._id = car_id
        self._turns = 1
        self._skipped_turns = skipped_turns
        self._start_pos = start_pos
        self._car_priority = car_priority
        self._x = 0
        self._y = 0
        self._final_x = 0
        self._final_y = 0
        self._unavailable_cells: list[list[bool]] = []

    def setup(self):
        self._x = self._start_pos
        self._y = utils.SIZE  # starts below the grid (entry row)
        self._final_x = utils.rand_no_gen.randint(0, utils.SIZE // 2 - 1) * 2
        self._final_y = 0

        self._unavailable_cells = [[False] * utils.SIZE for _ in range(utils.SIZE)]
        for i in range(1, utils.SIZE, 2):
            for j in range(1, utils.SIZE, 2):
                self._unavailable_cells[i][j] = True

        print(f"Starting {self.name} - going to ({self._final_x},{self._final_y})")
        self.send("intersection", utils.str_msg("position", self._x, self._y, self._id))

    def act(self, messages: list[Message]):
        if self._turns > self._skipped_turns:
            for message in messages:
                print(f"\t[{message.sender} -> {self.name}]: {message.content}")

                action, parameters = utils.parse_message_list(message.content)

                if action == "block":
                    print(f"\t[{self.name}]: waits")
                    self.send("intersection",
                              utils.str_msg("change", self._x, self._y, self._id))
                elif action == "move" and self._is_at_destination():
                    print(f"\t[{self.name}]: Arrived at destination")
                    self.send("intersection",
                              utils.str_msg("finish", self._x, self._y, self._id))
                    self.stop()
                elif action == "move":
                    self._move_to_destination(parameters)
                    self.send("intersection",
                              utils.str_msg("change", self._x, self._y, self._id))
        self._turns += 1

    # ── Movement logic ────────────────────────────────────────────

    def _move_to_destination(self, t: list[str]):
        left_cell_no_cars = int(t[0])
        up_cell_no_cars = int(t[1])
        right_cell_no_cars = int(t[2])
        left_cell_light = utils.TrafficLightState(t[3])
        up_cell_light = utils.TrafficLightState(t[4])
        right_cell_light = utils.TrafficLightState(t[5])

        dx = self._x - self._final_x
        dy = self._y - self._final_y
        new_x, new_y = self._x, self._y

        # No priority or not at an intersection
        if not self._is_intersection(self._x, self._y) or \
                self._car_priority == utils.CarPriorityState.NoPriority:
            if abs(dx) > abs(dy):
                new_x -= self._sign(dx)
            else:
                new_y -= self._sign(dy)

            if 0 <= new_x < utils.SIZE and 0 <= new_y < utils.SIZE and \
                    self._unavailable_cells[new_x][new_y]:
                if new_x == self._x:
                    # unavailable cell is up => goes left or right
                    if dx != 0:
                        candidate = self._x - self._sign(dx)
                        if 0 <= candidate < utils.SIZE:
                            new_x = candidate
                            new_y = self._y
                    elif self._x - 1 >= 0:
                        new_x = self._x - 1
                        new_y = self._y
                    elif self._x + 1 < utils.SIZE:
                        new_x = self._x + 1
                        new_y = self._y
                elif new_y == self._y:
                    # unavailable cell is right or left => goes up
                    if self._y - 1 >= 0:
                        new_y = self._y - 1
                        new_x = self._x

            self._x = new_x
            self._y = new_y

        # GreenLight priority
        elif self._car_priority == utils.CarPriorityState.GreenLight:
            dx = self._x - self._final_x
            if dx > 0:  # next direction is left
                if left_cell_light == utils.TrafficLightState.Green and left_cell_no_cars != -1:
                    self._x -= 1
                elif up_cell_light == utils.TrafficLightState.Green and up_cell_no_cars != -1:
                    self._y -= 1
                elif right_cell_light == utils.TrafficLightState.Green and right_cell_no_cars != -1:
                    self._x += 1
            elif dx < 0:  # next direction is right
                if right_cell_light == utils.TrafficLightState.Green and right_cell_no_cars != -1:
                    self._x += 1
                elif up_cell_light == utils.TrafficLightState.Green and up_cell_no_cars != -1:
                    self._y -= 1
                elif left_cell_light == utils.TrafficLightState.Green and left_cell_no_cars != -1:
                    self._x -= 1
            else:  # next direction is up
                if up_cell_light == utils.TrafficLightState.Green and up_cell_no_cars != -1:
                    self._y -= 1
                elif left_cell_light == utils.TrafficLightState.Green and left_cell_no_cars != -1:
                    self._x -= 1
                elif right_cell_light == utils.TrafficLightState.Green and right_cell_no_cars != -1:
                    self._x += 1

        # LowerTraffic priority
        elif self._car_priority == utils.CarPriorityState.LowerTraffic:
            dx = self._x - self._final_x
            min_index = self._get_min_cars_direction(
                left_cell_no_cars, up_cell_no_cars, right_cell_no_cars)

            if dx > 0:
                if left_cell_no_cars != -1 and min_index == 1:
                    self._x -= 1
                elif up_cell_no_cars != -1 and min_index == 2:
                    self._y -= 1
                elif right_cell_no_cars != -1 and min_index == 3:
                    self._x += 1
            elif dx < 0:
                if right_cell_no_cars != -1 and min_index == 3:
                    self._x += 1
                elif up_cell_no_cars != -1 and min_index == 2:
                    self._y -= 1
                elif left_cell_no_cars != -1 and min_index == 1:
                    self._x -= 1
            else:
                if up_cell_no_cars != -1 and min_index == 2:
                    self._y -= 1
                elif left_cell_no_cars != -1 and min_index == 1:
                    self._x -= 1
                elif right_cell_no_cars != -1 and min_index == 3:
                    self._x += 1

    @staticmethod
    def _get_min_cars_direction(left: int, up: int, right: int) -> int:
        min_val = 2**31
        min_index = 0
        if left != -1:
            min_val = left
            min_index = 1
        if up != -1 and up < min_val:
            min_val = up
            min_index = 2
        if right != -1 and right < min_val:
            min_index = 3
        return min_index

    def _is_at_destination(self) -> bool:
        return self._x == self._final_x and self._y == self._final_y

    @staticmethod
    def _is_intersection(x: int, y: int) -> bool:
        return y > 3 and y < utils.SIZE - 3 and x % 2 == 0

    @staticmethod
    def _sign(val: int) -> int:
        if val > 0:
            return 1
        elif val < 0:
            return -1
        return 0
