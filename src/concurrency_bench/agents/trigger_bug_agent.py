from concurrency_bench.agents.base import ConcurrencyAgent


class TriggerBugAgent(ConcurrencyAgent):
    """Agent specialized in triggering and reproducing concurrency bugs.

    This agent writes code or test cases that reliably reproduce concurrency
    issues to demonstrate their existence.
    """

    def task_description(self) -> str:
        # TODO: move this to a prompts file
        return """Your task is to trigger and reproduce concurrency bugs in the codebase.

Your goal is to:
- Analyze the code for potential concurrency issues
- Modify existing code to reliably reproduce the bugs
- Demonstrate race conditions, deadlocks, or other concurrency problems
- The bug is triggered when the program exits with an AssertionError

Constraints:
- You may ONLY modify existing files in the workspace. Do NOT create new files.
- You may use sleep, locks, or condition variables to enforce specific thread scheduling that triggers the bug.
- Do NOT add print statements or other debugging output.
- Do NOT change the original behavior or logic of the program beyond what is necessary to expose the concurrency bug.

Create minimal modifications that reliably trigger the concurrency issues.
When complete, use the finish tool to report what bugs you were able to trigger and how."""
