import sys
from concurrency_bench.tasks.task import ConcurrencyTask, TaskOutput
from concurrency_bench.tasks.loaders.real_world_junit_loader import RealWorldJUnitLoader


class FixBugTask(ConcurrencyTask):
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
                    # "--iterations=1000",
                ],
            )
        # Original task should fail with Fray
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
