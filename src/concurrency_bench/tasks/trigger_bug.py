from concurrency_bench.tasks.task import ConcurrencyTask, TaskOutput


class TriggerBugTask(ConcurrencyTask):
    def setup(self):
        """Set up the environment for the trigger bug task."""
        pass

    def verify(self) -> TaskOutput:
        """Verify that the concurrency bug was successfully triggered.

        Returns:
            TaskOutput: Result indicating if the bug was triggered.
        """
        pass
