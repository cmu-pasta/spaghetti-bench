from pathlib import Path


class TaskLoader:
    def __init__(self, task_name: str):
        self._task_name = task_name

    def build(self, workdir: Path):
        pass

    def run(self, workdir: Path) -> tuple[str, bool]:
        pass
