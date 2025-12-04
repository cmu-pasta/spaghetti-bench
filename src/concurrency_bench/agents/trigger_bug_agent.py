from concurrency_bench.agents.base import ConcurrencyAgent


class TriggerBugAgent(ConcurrencyAgent):
    """Agent specialized in triggering and reproducing concurrency bugs.

    This agent writes code or test cases that reliably reproduce concurrency
    issues to demonstrate their existence.
    """

    def task_description(self) -> str:
        # TODO: move this to a prompts file
        return """Your task is to write code or test cases that trigger and reproduce concurrency bugs in the codebase.

Your goal is to:
- Analyze the code for potential concurrency issues
- Create test cases or scripts that reliably reproduce the bugs
- Demonstrate race conditions, deadlocks, or other concurrency problems
- Show the bug occurring through execution or test failures

Create minimal, reproducible examples that clearly demonstrate the concurrency issues.
When complete, use the finish tool to report what bugs you were able to trigger and how."""
