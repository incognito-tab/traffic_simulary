"""
Utility constants, enums, and helper functions for the traffic simulation.
Direct port of Utils.cs.
"""

import random
from enum import Enum


# ── Constants ──────────────────────────────────────────────────────
SIZE = 7
NO_CARS = 100
NO_MS_PER_TURN = 100
NO_CARS_PER_CELL = 3                          # grid with NoCarsPerCell*NoCarsPerCell cars
MAX_NO_CARS_PER_CELL = NO_CARS_PER_CELL * NO_CARS_PER_CELL
NO_STARTING_POINTS = (SIZE + 1) // 2
LIGHT_SWITCHING_TIME = 5                      # number of turns to change light
MULTIPLE_CARS_PER_TURN = True                 # if there are multiple spawned cars per turn


# ── Enums ──────────────────────────────────────────────────────────
class TrafficLightState(Enum):
    Green = "Green"
    Red = "Red"
    Unavailable = "Unavailable"


class CarPriorityState(Enum):
    NoPriority = "NoPriority"
    GreenLight = "GreenLight"
    LowerTraffic = "LowerTraffic"


class TrafficLightIntelligenceState(Enum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


# ── Module-level state ────────────────────────────────────────────
_intelligence_state = TrafficLightIntelligenceState.L0
rand_no_gen = random.Random()


def set_traffic_light_intelligence(state: TrafficLightIntelligenceState):
    global _intelligence_state
    _intelligence_state = state


# ── Message parsing ───────────────────────────────────────────────
def parse_message_list(content: str):
    """Parse message into (action, list_of_parameters)."""
    t = content.split()
    action = t[0]
    parameters = t[1:]
    return action, parameters


def parse_message_str(content: str):
    """Parse message into (action, parameter_string)."""
    t = content.split()
    action = t[0]
    parameters = " ".join(t[1:]) if len(t) > 1 else ""
    return action, parameters


def parse_message_matrix(content: str, x: int, y: int):
    """Parse message into (action, 2D matrix) based on intelligence level."""
    t = content.split()
    idx = 1
    action = t[0]
    parameters = [[0] * SIZE for _ in range(SIZE)]

    if _intelligence_state == TrafficLightIntelligenceState.L0:
        pass
    elif _intelligence_state == TrafficLightIntelligenceState.L1:
        for i in range(SIZE):
            for j in range(SIZE):
                if x - 1 <= i <= x + 1 and y - 1 <= j <= y + 1:
                    parameters[i][j] = int(t[idx])
                    idx += 1
                else:
                    parameters[i][j] = -1
    elif _intelligence_state == TrafficLightIntelligenceState.L2:
        for i in range(SIZE):
            for j in range(SIZE):
                if x - 2 <= i <= x + 2 and y - 2 <= j <= y + 2:
                    parameters[i][j] = int(t[idx])
                    idx += 1
                else:
                    parameters[i][j] = -1
    elif _intelligence_state == TrafficLightIntelligenceState.L3:
        for i in range(SIZE):
            for j in range(SIZE):
                parameters[i][j] = int(t[idx])
                idx += 1

    return action, parameters


# ── String builders ───────────────────────────────────────────────
def str_msg(*args):
    """Build a space-separated message string from multiple arguments."""
    return " ".join(str(a) for a in args)


def build_message(matrix, message: str, x: int, y: int) -> str:
    """Build a message string with traffic data based on intelligence level."""
    parts = [message]

    if _intelligence_state == TrafficLightIntelligenceState.L0:
        pass
    elif _intelligence_state == TrafficLightIntelligenceState.L1:
        for i in range(x - 1, x + 2):
            for j in range(y - 1, y + 2):
                if 0 <= i < SIZE and 0 <= j < SIZE:
                    parts.append(str(matrix[i][j]))
                else:
                    parts.append(str(-1))
    elif _intelligence_state == TrafficLightIntelligenceState.L2:
        for i in range(x - 2, x + 3):
            for j in range(y - 2, y + 3):
                if 0 <= i < SIZE and 0 <= j < SIZE:
                    parts.append(str(matrix[i][j]))
                else:
                    parts.append(str(-1))
    elif _intelligence_state == TrafficLightIntelligenceState.L3:
        for i in range(len(matrix)):
            for j in range(len(matrix[0])):
                parts.append(str(matrix[i][j]))

    return " ".join(parts)


# ── Utilities ─────────────────────────────────────────────────────
def map_value(x: int, in_min: int, in_max: int, out_min: int, out_max: int) -> int:
    """Linear interpolation / mapping from one range to another."""
    if in_max == in_min:
        return out_min
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min


def print_2d_array(matrix):
    """Print a 2D array to console."""
    for row in matrix:
        print("\t".join(str(v) for v in row))
