from concurrency_bench.tasks.task import ConcurrencyTask, TaskOutput


class TriggerBugTask(ConcurrencyTask):
    def setup(self):
        """Set up the environment for the trigger bug task."""
        self._loader.build(self._workdir)
        assert self._loader.run(self._workdir)[1]

    def verify(self) -> TaskOutput:
        """Verify that the concurrency bug was successfully triggered.

        Returns:
            TaskOutput: Result indicating if the bug was triggered.
        """
        [output, result] = self._loader.run(self._workdir)
        print("The output of the bug-triggering run:")
        print(output)
        return TaskOutput(success=not result)
