from dataclasses import dataclass
from pathlib import Path


@dataclass
class TaskOutput:
    success: bool


class ConcurrencyTask:
    def __init__(self, workdir: Path):
        pass

    def setup(self):
        pass

    def verify(self) -> TaskOutput:
        pass
