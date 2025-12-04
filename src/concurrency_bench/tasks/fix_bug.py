from concurrency_bench.tasks.task import ConcurrencyTask, TaskOutput


class FixBugTask(ConcurrencyTask):
    def setup(self):
        """Set up the environment for the fix bug task."""
        pass

    def verify(self) -> TaskOutput:
        """Verify that the concurrency bug has been fixed.

        Returns:
            TaskOutput: Result indicating if the fix was successful.
        """
        pass
