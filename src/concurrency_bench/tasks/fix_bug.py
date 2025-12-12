import sys
import re
from concurrency_bench.tasks.task import ConcurrencyTask, TaskOutput
from concurrency_bench.tasks.loaders.real_world_junit_loader import RealWorldJUnitLoader


def extract_stack_trace(fray_output: str) -> str | None:
    """Extract the stack trace from Fray output when an assertion fails.

    Returns:
        The stack trace string or None if not found.
    """
    # Look for error messages with stack traces
    # Pattern: "Error: <exception>" followed by "Thread:" and the stack trace
    pattern = r"\[INFO\]: Error: (.+?)(?=\n\n|\Z)"
    match = re.search(pattern, fray_output, re.DOTALL)

    if match:
        return match.group(1).strip()

    return None


class FixBugTask(ConcurrencyTask):
    def __init__(self, workdir, loader):
        super().__init__(workdir, loader)
        self.stack_trace = None

    def setup(self) -> str:
        """Set up the environment for the fix bug task.

        Returns:
            str: Combined stdout/stderr from setup.
        """
        # Clone repository if loader supports it (for real-world loaders)
        if hasattr(self._loader, "clone_repo"):
            self._loader.clone_repo(self._workdir)

        self._loader.build(self._workdir)

        # Real-world loaders handle Fray invocation internally
        if isinstance(self._loader, RealWorldJUnitLoader):
            [output, passes] = self._loader.run(self._workdir)
        else:
            # SCTBench-style loaders use simple command-line invocation
            [output, passes] = self._loader.run(
                self._workdir,
                run_command=[
                    "fray",
                    "-cp",
                    ".",
                    f"{self._loader._task_name}",
                    # TODO: Add Fray specific args after testing
                    # "--scheduler=pos",
                    # "--iter=1000",
                ],
            )

        # Extract stack trace if the test failed
        if not passes:
            self.stack_trace = extract_stack_trace(output)

        print(f"Stack trace: {self.stack_trace}")

        # Original task should fail with Fray
        # print(output)
        assert not passes, "Setup failed: Fray should trigger the original bug."
        return output

    def verify(self) -> TaskOutput:
        """Verify that the concurrency bug has been fixed.

        Returns:
            TaskOutput: Result indicating if the fix was successful.
        """
        self._loader.build(self._workdir)

        # Real-world loaders handle Fray invocation internally
        if isinstance(self._loader, RealWorldJUnitLoader):
            [output, passes] = self._loader.run(self._workdir)
        else:
            # SCTBench-style loaders use simple command-line invocation
            [output, passes] = self._loader.run(
                self._workdir,
                run_command=[
                    "fray",
                    "-cp",
                    ".",
                    f"{self._loader._task_name}",
                    # TODO: Add Fray specific args after testing
                    # "--scheduler=pos",
                    # "--iterations=1000",
                ],
            )
        print("The output of the bug-triggering run:")
        print(output)
        return TaskOutput(success=passes, verify_output=output)
