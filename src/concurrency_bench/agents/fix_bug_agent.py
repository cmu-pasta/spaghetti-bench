from concurrency_bench.agents.base import ConcurrencyAgent


class FixBugAgent(ConcurrencyAgent):
    """Agent specialized in fixing concurrency bugs.

    This agent identifies and fixes concurrency issues like race conditions,
    deadlocks, and other threading/async problems.
    """

    def task_description(self) -> str:
        # TODO: move this to a prompts file
        prompt = """Your task is to identify and fix concurrency bugs in the codebase.
"""

        # Add test-specific information for real-world projects
        if "test_class" in self.task_info and "test_method" in self.task_info:
            prompt += f"""
The test that is failing (nondeterministically) is:
- Test class: {self.task_info['test_class']}
- Test method: {self.task_info['test_method']}

"""

        prompt += """Look for common concurrency issues such as:
- Race conditions
- Deadlocks
- Thread safety violations
- Missing synchronization
- Improper use of locks or semaphores
- Async/await issues

Analyze the code, identify the root cause of any concurrency bugs, and implement fixes.
You are NOT allowed to change the number of threads or the number of iterations in any loops. In general, do NOT significantly change the behavior of the program
other than the logic of the fix.
When complete, use the finish tool to report what you found and fixed."""

        return prompt
