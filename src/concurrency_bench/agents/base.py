"""Base agent for concurrency benchmark tasks."""

import os
from abc import ABC, abstractmethod
from pathlib import Path

from openhands.sdk import LLM, Agent, Conversation
from openhands.sdk.conversation.types import ConversationCallbackType
from openhands.sdk.tool import Tool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.terminal import TerminalTool

from concurrency_bench.agents.noop_agent import NoopAgent
from concurrency_bench.task_config import TaskConfig
from concurrency_bench.tasks.task import ConcurrencyTask

NOOP_AGENT_ID = "noop"


class ConcurrencyAgent(ABC):
    """Base class for concurrency benchmark agents."""

    def __init__(
        self,
        workdir: Path,
        model_id: str,
        task_config: TaskConfig,
        task_instance: ConcurrencyTask,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        """Initialize the ConcurrencyAgent.

        Args:
            workdir: Working directory for the agent.
            model_id: The model ID to use (e.g., "bedrock/bedrock/global.anthropic.claude-sonnet-4-5-20250929-v1:0").
            api_key: API key for the LLM provider (defaults to env var).
            task_config: Configuration for the task.
            task_instance: Instance of the concurrency task.
        """
        self.workdir = workdir
        self.model_id = model_id
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.task_config = task_config
        self.task_instance = task_instance
        self.agent = None

    @abstractmethod
    def task_description(self) -> str:
        """Build the task description for the agent.

        Returns:
            str: Task description with instructions for the agent.
        """
        pass

    def add_tools(self, tools: list) -> list:
        """Add additional tools to the base tool list.

        Override this method to add custom tools like Fray tools.

        Args:
            tools: List of base tools

        Returns:
            list: Extended list of tools
        """
        return tools

    def configure_tools(self):
        """Configure tools for the agent. Overriding this
        would be useful for adding specific concurrency tools like Fray.

        Returns:
            list: List of tools for the agent.
        """
        tools = [
            Tool(name=TerminalTool.name, params={"terminal_type": "subprocess"}),
            Tool(name=FileEditorTool.name),
            Tool(name=TaskTrackerTool.name),
        ]

        return self.add_tools(tools)

    def initialize_agent(self) -> Agent | NoopAgent:
        if self.model_id == NOOP_AGENT_ID:
            self.agent = NoopAgent()
            return self.agent
        llm = LLM(
            model=self.model_id,
            api_key=self.api_key,
        )

        tools = self.configure_tools()

        self.agent = Agent(
            llm=llm,
            tools=tools,
        )

        return self.agent

    def run_agent(self):
        if self.agent is None:
            self.initialize_agent()

        if type(self.agent) is Agent:
            conversation = Conversation(agent=self.agent, workspace=self.workdir)
            description = self.task_description()
            conversation.send_message(description)
            conversation.run()
            return conversation
        if type(self.agent) is NoopAgent:
            return self.agent.dummy_conversation()
