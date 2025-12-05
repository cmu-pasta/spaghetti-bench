from pathlib import Path
from concurrency_bench.tasks.loaders.task_loader import TaskLoader
from subprocess import run


AGENT_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "unhandled_exception_reporter"
    / "UnhandledExceptionReporterAgent.jar"
)


class SCTBenchLoader(TaskLoader):
    def build(self, workdir: Path):
        run(["javac", f"{self._task_name}.java"], cwd=workdir, check=True)

    def run(self, workdir: Path) -> tuple[str, bool]:
        result = run(
            [
                "java",
                "-ea",
                "-javaagent:" + str(AGENT_PATH),
                "-cp",
                ".",
                f"{self._task_name}",
            ],
            cwd=workdir,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout + result.stderr, result.returncode == 0
        result = run(
            ["java", "-ea", "-cp", ".", f"{self._task_name}"],
            cwd=workdir,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout + result.stderr, result.returncode == 0


class SCTBenchFixLoader(SCTBenchLoader):
    def run(self, workdir: Path) -> tuple[str, bool]:
        # Run Fray with POS for fixed time limit for now
        result = run(
            [
                "fray",
                "-cp",
                ".",
                f"{self._task_name}",
                "--scheduler=pos",
                "--iterations=1000",
            ],
            cwd=workdir,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout + result.stderr, result.returncode == 0
