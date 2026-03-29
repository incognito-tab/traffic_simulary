"""
Traffic Simulation – Entry point.
Direct port of Program.cs.

Reads config from config.json, creates the environment with agents, and starts the simulation.
"""

import json
import os
import sys

import utils
from agent_framework import TurnBasedEnvironment
from car_agent import CarAgent
from intersection_agent import IntersectionAgent
from traffic_light_agent import TrafficLightAgent


def main():
    # ── Read config ───────────────────────────────────────────────
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    with open(config_path, "r") as f:
        config = json.load(f)

    # Traffic Light Intelligence
    traffic_light_intelligence = utils.TrafficLightIntelligenceState(
        config["TrafficLightIntelligence"]
    )
    utils.set_traffic_light_intelligence(traffic_light_intelligence)

    # Cars Rate
    cars_rate_names = ["CarsRateA", "CarsRateB", "CarsRateC", "CarsRateD"]
    cars_rate = [config[name] for name in cars_rate_names[:utils.NO_STARTING_POINTS]]

    # Cars Priority
    cars_priority = utils.CarPriorityState(config["CarsPriority"])

    # ── Build environment ─────────────────────────────────────────
    env = TurnBasedEnvironment(delay_after_turn=0, ms_per_turn=utils.NO_MS_PER_TURN)
    intersection_agent = IntersectionAgent(total_cars=utils.NO_CARS)

    # Traffic lights
    index = 0
    initial_state = utils.TrafficLightState.Green
    for j in range(2, utils.SIZE - 1, 2):
        for i in range(0, utils.SIZE, 2):
            tl_agent = TrafficLightAgent(
                index, i, j, utils.LIGHT_SWITCHING_TIME, initial_state
            )
            env.add(tl_agent, f"trafficLight{index}")
            index += 1

            # Alternate state
            if initial_state == utils.TrafficLightState.Green:
                initial_state = utils.TrafficLightState.Red
            else:
                initial_state = utils.TrafficLightState.Green

    # Cars
    car_index = 0
    skipped_turns = 1
    no_cars_left = utils.NO_CARS

    while no_cars_left != 0:
        for i in range(utils.NO_STARTING_POINTS):
            if no_cars_left == 0:
                break
            for j in range(cars_rate[i]):
                if no_cars_left == 0:
                    break
                car_agent = CarAgent(car_index, skipped_turns, i * 2, cars_priority)
                env.add(car_agent, f"explorer{car_index}")
                no_cars_left -= 1
                car_index += 1
            if not utils.MULTIPLE_CARS_PER_TURN:
                skipped_turns += 1
        if utils.MULTIPLE_CARS_PER_TURN:
            skipped_turns += 1

    env.add(intersection_agent, "intersection")

    # ── Start simulation ──────────────────────────────────────────
    print(f"Starting simulation with {utils.NO_CARS} cars, "
          f"intelligence={traffic_light_intelligence.value}, "
          f"priority={cars_priority.value}")
    env.start()


if __name__ == "__main__":
    main()
