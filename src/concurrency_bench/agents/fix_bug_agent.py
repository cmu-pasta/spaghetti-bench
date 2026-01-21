from concurrency_bench.agents.base import ConcurrencyAgent
from concurrency_bench.tools.fray_tools import ReplayFrayTool, RerunFrayTool


class FixBugAgent(ConcurrencyAgent):
    """Agent specialized in fixing concurrency bugs.

    This agent identifies and fixes concurrency issues like race conditions,
    deadlocks, and other threading/async problems.
    """

    def __init__(self, *args, enable_fray_tools: bool = False, **kwargs):
        """Initialize the FixBugAgent.

        Args:
            enable_fray_tools: If True, add Fray-specific tools for debugging.
            *args, **kwargs: Passed to ConcurrencyAgent.__init__
        """
        super().__init__(*args, **kwargs)
        self.enable_fray_tools = enable_fray_tools

    def task_description(self) -> str:
        # TODO: move this to a prompts file
        prompt = """Your task is to identify and fix concurrency bugs in the codebase.
"""

        # Add test-specific information for real-world projects
        prompt += f"""
The test that is failing (nondeterministically) is:
- Test class: {self.task_config.test_class}
- Test method: {self.task_config.test_method}

"""
        if self.task_instance.get_stdout().strip():
            prompt += f"""
When we ran Fray (a concurrency testing tool) to trigger the bug, we got the following stdout output:

```
{self.task_instance.get_stdout()}
```

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
"""

        # Add Fray tools instructions if enabled
        if self.enable_fray_tools:
            fray_command = self.task_instance.get_fray_command_template()
            prompt += f"""
You have access to the special Fray debugging tool:
- rerun_fray: Rerun Fray to verify your fix works

The Fray command to use for this test is:
```
{fray_command}
```

These tools are useful for iterative debugging:
1. Add debug print statements
2. Rebuild (javac or build system)
3. Use replay_fray to see the prints in the buggy interleaving
4. Analyze and fix
5. Use rerun_fray to verify the fix

IMPORTANT: After making changes and rebuilding, use the exact Fray command provided above.

"""

        prompt += (
            "When complete, use the finish tool to report what you found and fixed."
        )

        return prompt

    def add_tools(self, tools: list) -> list:
        """Add Fray tools if enabled.

        Args:
            tools: List of base tools

        Returns:
            list: Extended list of tools with Fray tools if enabled
        """
        if not self.enable_fray_tools:
            return tools

        # Add registered FrayTools (which includes both rerun_fray and replay_fray)
        from openhands.sdk.tool import Tool

        # The FrayTools factory function is registered in fray_tools.py
        # It returns both rerun_fray and replay_fray tools
        tools.append(Tool(name="FrayTools"))

        return tools
