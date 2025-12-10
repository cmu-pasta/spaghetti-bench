from concurrency_bench.tasks.task import ConcurrencyTask, TaskOutput


class TriggerBugTask(ConcurrencyTask):
    def setup(self):
        """Set up the environment for the trigger bug task."""
        self._loader.build(self._workdir)
        run_result = self._loader.run(self._workdir)
        print("The output of the setup run:")
        print(run_result[0])
        assert run_result[1], "Setup failed: could not run the task."

    def verify(self) -> TaskOutput:
        """Verify that the concurrency bug was successfully triggered.

        Returns:
            TaskOutput: Result indicating if the bug was triggered.
        """
        self._loader.build(self._workdir)
        [output, passes] = self._loader.run(self._workdir)
        print("The output of the bug-triggering run:")
        print(output)
        return TaskOutput(success=not passes)
