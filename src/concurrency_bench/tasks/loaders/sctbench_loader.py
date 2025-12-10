from pathlib import Path
from typing import List, Optional
from concurrency_bench.tasks.loaders.task_loader import TaskLoader
from subprocess import run


class SCTBenchLoader(TaskLoader):
    def build(self, workdir: Path):
        run(["javac", f"{self._task_name}.java"], cwd=workdir, check=True)

    def run(
        self, workdir: Path, run_command: Optional[List[str]] = None
    ) -> tuple[str, bool]:
        if run_command:
            result = run(
                run_command, cwd=workdir, capture_output=True, text=True, check=False
            )
        else:
            result = run(
                ["java", "-ea", "-cp", ".", f"{self._task_name}"],
                cwd=workdir,
                capture_output=True,
                text=True,
                check=False,
            )
        return result.stdout + result.stderr, result.returncode == 0
