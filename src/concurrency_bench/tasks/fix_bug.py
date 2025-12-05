from concurrency_bench.tasks.task import ConcurrencyTask, TaskOutput


class FixBugTask(ConcurrencyTask):
    def setup(self):
        """Set up the environment for the fix bug task."""
        self._loader.build(self._workdir)
        assert self._loader.run(self._workdir)[1]

    def verify(self) -> TaskOutput:
        """Verify that the concurrency bug has been fixed.

        Returns:
            TaskOutput: Result indicating if the fix was successful.
        """
        self._loader.build(self._workdir)
        [output, result] = self._loader.run(self._workdir)
        print("The output of the bug-triggering run:")
        print(output)
        return TaskOutput(success=result)
