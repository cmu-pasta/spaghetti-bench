from dataclasses import dataclass
from pathlib import Path

from concurrency_bench.tasks.loaders.task_loader import TaskLoader


@dataclass
class TaskOutput:
    success: bool


class ConcurrencyTask:
    def __init__(self, workdir: Path, loader: TaskLoader):
        self._workdir = workdir
        self._loader = loader
        pass

    def setup(self):
        pass

    def verify(self) -> TaskOutput:
        pass
