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
    def dummy_conversation(self) -> Any:
        return DummyConversation()
