from concurrency_bench.agents.base import ConcurrencyAgent


class FixBugAgent(ConcurrencyAgent):
    """Agent specialized in fixing concurrency bugs.

    This agent identifies and fixes concurrency issues like race conditions,
    deadlocks, and other threading/async problems.
    """

    def task_description(self) -> str:
        # TODO: move this to a prompts file
        return """Your task is to identify and fix concurrency bugs in the codebase.

Look for common concurrency issues such as:
- Race conditions
- Deadlocks
- Thread safety violations
- Missing synchronization
- Improper use of locks or semaphores
- Async/await issues

Analyze the code, identify the root cause of any concurrency bugs, and implement fixes.
When complete, use the finish tool to report what you found and fixed."""
