from pathlib import Path
from typing import Any


class DummyState:
    def __init__(self) -> None:
        self.events = []


class DummyConversation:
    def __init__(self) -> None:
        self.id = "noop-conversation"
        self.state = DummyState()
        pass


class NoopAgent:
    def dummy_conversation(self) -> DummyConversation:
        return DummyConversation()


class GoldenAgent:
    def run(self, workdir: Path, patch_url: str) -> DummyConversation:
        import subprocess

        patch_file = workdir / "repo" / "golden_patch.diff"
        subprocess.run(
            ["curl", "-o", str(patch_file), patch_url],
            check=True,
        )
        subprocess.run(
            ["git", "apply", str(patch_file)],
            cwd=workdir / "repo",
            check=True,
        )
        return DummyConversation()
