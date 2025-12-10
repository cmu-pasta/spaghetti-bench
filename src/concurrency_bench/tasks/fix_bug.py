from concurrency_bench.tasks.task import ConcurrencyTask, TaskOutput


class FixBugTask(ConcurrencyTask):
    def setup(self) -> str:
        """Set up the environment for the fix bug task.

        Returns:
            str: Combined stdout/stderr from setup.
        """
        self._loader.build(self._workdir)
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
