"""Concurrency benchmark agents."""

# Import tools to ensure they're registered with OpenHands SDK
from concurrency_bench import tools  # noqa: F401

from concurrency_bench.agents.base import ConcurrencyAgent
from concurrency_bench.agents.fix_bug_agent import FixBugAgent
from concurrency_bench.agents.trigger_bug_agent import TriggerBugAgent

__all__ = ["ConcurrencyAgent", "FixBugAgent", "TriggerBugAgent"]
