"""
Lightweight turn-based multi-agent framework.
Replaces the C# ActressMas library.
"""

from collections import deque
from dataclasses import dataclass, field
import time
import threading


@dataclass
class Message:
    """A message sent between agents."""
    sender: str
    content: str


class TurnBasedAgent:
    """Base class for turn-based agents."""

    def __init__(self):
        self.name: str = ""
        self._environment: 'TurnBasedEnvironment' = None
        self._running: bool = True

    def setup(self):
        """Called once when the agent is first added to the environment."""
        pass

    def act(self, messages: list[Message]):
        """Called each turn with queued messages."""
        pass

    def send(self, receiver: str, content: str):
        """Send a message to another agent by name."""
        if self._environment:
            self._environment._deliver_message(self.name, receiver, content)

    def stop(self):
        """Stop this agent from participating in future turns."""
        self._running = False


class TurnBasedEnvironment:
    """
    Manages agents and runs the turn-based simulation loop.
    Each turn: all agents act on their queued messages, then the cycle repeats.
    """

    def __init__(self, delay_after_turn: int = 0, ms_per_turn: int = 100):
        self._agents: dict[str, TurnBasedAgent] = {}
        self._message_queues: dict[str, deque[Message]] = {}
        self._delay_after_turn = delay_after_turn
        self._ms_per_turn = ms_per_turn
        self._running = False

    def add(self, agent: TurnBasedAgent, name: str):
        """Register an agent with the given name."""
        agent.name = name
        agent._environment = self
        self._agents[name] = agent
        self._message_queues[name] = deque()

    def _deliver_message(self, sender: str, receiver: str, content: str):
        """Queue a message for delivery next turn."""
        if receiver in self._message_queues:
            self._message_queues[receiver].append(Message(sender=sender, content=content))

    def start(self):
        """Run the simulation: setup all agents, then loop turns until no agents remain."""
        self._running = True

        # Setup phase
        for name, agent in list(self._agents.items()):
            agent.setup()

        # Turn loop
        turn = 0
        while self._running:
            turn += 1
            active_agents = {n: a for n, a in self._agents.items() if a._running}

            if not active_agents:
                break

            # Collect messages for this turn
            turn_messages: dict[str, list[Message]] = {}
            for name in active_agents:
                msgs = list(self._message_queues[name])
                self._message_queues[name].clear()
                turn_messages[name] = msgs

            # Each agent acts
            for name, agent in active_agents.items():
                if not self._running:
                    break
                if agent._running:
                    agent.act(turn_messages.get(name, []))

            # Check if any agents are still running
            if not any(a._running for a in self._agents.values()):
                break

            # Delay between turns
            if self._ms_per_turn > 0:
                time.sleep(self._ms_per_turn / 1000.0)

        self._running = False
        print("Simulation finished.")

    def stop(self):
        """Stop the simulation loop."""
        self._running = False
