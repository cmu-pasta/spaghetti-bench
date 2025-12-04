"""Base agent for concurrency benchmark tasks."""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from openhands.sdk import Agent, LLM, Conversation
from openhands.tools.preset.default import get_default_tools


class ConcurrencyAgent(ABC):
    """Base class for concurrency benchmark agents."""

    def __init__(
        self,
        workdir: Path,
        model_id: str,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        """Initialize the ConcurrencyAgent.

        Args:
            workdir: Working directory for the agent.
            model_id: The model ID to use (e.g., "bedrock/bedrock/global.anthropic.claude-sonnet-4-5-20250929-v1:0").
            api_key: API key for the LLM provider (defaults to env var).
        """
        self.workdir = workdir
        self.model_id = model_id
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.agent = None

    @abstractmethod
    def task_description(self) -> str:
        """Build the task description for the agent.

        Returns:
            str: Task description with instructions for the agent.
        """
        pass

    def configure_tools(self):
        """Configure tools for the agent. Overriding this
        would be useful for adding specific concurrency tools like Fray.

        Returns:
            list: List of tools for the agent.
        """
        # Use default tools: Terminal, FileEditor, TaskTracker
        # Disable browser as it's typically not needed for concurrency tasks
        return get_default_tools(enable_browser=False)

    def initialize_agent(self) -> Agent:
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

        conversation = Conversation(agent=self.agent, workspace=self.workdir)
        description = self.task_description()
        conversation.send_message(description)
        conversation.run()

        return conversation
