from concurrency_bench.tasks.task import ConcurrencyTask, TaskOutput


class TriggerBugTask(ConcurrencyTask):
    def setup(self) -> str:
        """Set up the environment for the trigger bug task.

        Returns:
            str: Combined stdout/stderr from setup.
        """
        self._loader.build(self._workdir)
        run_result = self._loader.run(self._workdir, run_command=None)
        print("The output of the setup run:")
        print(run_result[0])
        assert run_result[1], "Setup failed: could not run the task."
        return run_result[0]

    def verify(self) -> TaskOutput:
        """Verify that the concurrency bug was successfully triggered.

        Returns:
            TaskOutput: Result indicating if the bug was triggered.
        """
        self._loader.build(self._workdir)
        [output, passes] = self._loader.run(self._workdir, run_command=None)
        print("The output of the bug-triggering run:")
        print(output)
        return TaskOutput(success=not passes, verify_output=output)
