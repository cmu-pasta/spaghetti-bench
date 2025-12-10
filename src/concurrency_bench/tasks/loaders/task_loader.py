from pathlib import Path
from typing import List, Optional


class TaskLoader:
    def __init__(self, task_name: str):
        self._task_name = task_name

    def build(self, workdir: Path):
        pass

    def run(
        self, workdir: Path, run_command: Optional[List[str]] = None
    ) -> tuple[str, bool]:
        pass
