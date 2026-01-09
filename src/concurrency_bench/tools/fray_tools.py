"""Fray-specific tools for debugging concurrency bugs."""

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import Field

if TYPE_CHECKING:
    from openhands.sdk.conversation.state import ConversationState

from openhands.sdk.llm import ImageContent, TextContent
from openhands.sdk.tool import (
    Action,
    Observation,
    ToolDefinition,
    ToolExecutor,
    register_tool,
)
from openhands.tools.terminal.impl import TerminalExecutor
from openhands.tools.terminal.definition import TerminalAction


class RerunFrayAction(Action):
    """Schema for rerunning Fray to verify the fix."""

    command: str = Field(
        description="The fray command to run (e.g., 'fray -cp . Reorder3Bad' or 'fray -cp <classpath> org.pastalab.fray.helpers.JUnitRunner ...')"
    )


class RerunFrayObservation(Observation):
    """Observation from rerunning Fray."""

    command: str = Field(description="The fray command that was executed")
    exit_code: int = Field(description="The exit code from running the command")

    @property
    def to_llm_content(self) -> Sequence[TextContent | ImageContent]:
        llm_content: list[TextContent | ImageContent] = []

        if self.is_error:
            llm_content.append(TextContent(text=self.ERROR_MESSAGE_HEADER))

        result = f"Command: {self.command}\n\n{self.text}\n\n"
        if self.exit_code == 0:
            result += "✅ Test PASSED - No concurrency bug detected"
        else:
            result += "❌ Test FAILED - Concurrency bug still present"

        llm_content.append(TextContent(text=result))
        return llm_content


class ReplayFrayAction(Action):
    """Schema for replaying the last Fray recording."""

    command: str = Field(
        description="The fray command to run with --replay flag (e.g., 'fray -cp . Reorder3Bad --replay /tmp/report/recording')"
    )
    replay_path: str = Field(
        default="/tmp/report/recording",
        description="Path to the Fray recording file to replay. Default is /tmp/report/recording which is the last recording.",
    )


class ReplayFrayObservation(Observation):
    """Observation from replaying Fray."""

    command: str = Field(description="The fray command that was executed")
    exit_code: int = Field(description="The exit code from running the command")

    @property
    def to_llm_content(self) -> Sequence[TextContent | ImageContent]:
        llm_content: list[TextContent | ImageContent] = []

        if self.is_error:
            llm_content.append(TextContent(text=self.ERROR_MESSAGE_HEADER))

        result = f"Command: {self.command}\n\n{self.text}\n\n"
        if self.exit_code == 0:
            result += "✅ Replay PASSED - No concurrency bug detected"
        else:
            result += "❌ Replay FAILED - Concurrency bug reproduced"

        llm_content.append(TextContent(text=result))
        return llm_content


class RerunFrayExecutor(ToolExecutor):
    """Executor for rerunning Fray tests."""

    def __init__(self, terminal_executor: TerminalExecutor):
        self.terminal_executor = terminal_executor

    def __call__(self, action: RerunFrayAction, conversation=None) -> RerunFrayObservation:
        """Execute Fray rerun."""
        try:
            # Execute the command via terminal (synchronous call)
            terminal_action = TerminalAction(command=action.command)
            terminal_obs = self.terminal_executor(terminal_action, conversation)

            return RerunFrayObservation(
                content=[TextContent(text=terminal_obs.text)],
                command=action.command,
                exit_code=terminal_obs.metadata.exit_code,
                is_error=terminal_obs.metadata.exit_code != 0,
            )
        except Exception as e:
            return RerunFrayObservation(
                content=[TextContent(text=f"Fray execution failed: {str(e)}")],
                command=action.command,
                exit_code=-1,
                is_error=True,
            )


class ReplayFrayExecutor(ToolExecutor):
    """Executor for replaying Fray recordings."""

    def __init__(self, terminal_executor: TerminalExecutor):
        self.terminal_executor = terminal_executor

    def __call__(self, action: ReplayFrayAction, conversation=None) -> ReplayFrayObservation:
        """Execute Fray replay."""
        # Check if replay file exists
        replay_path = Path(action.replay_path)
        if not replay_path.exists():
            return ReplayFrayObservation(
                content=[TextContent(text=f"Replay file not found: {action.replay_path}\nMake sure you've run Fray in exploration mode first to generate a recording.")],
                command=action.command,
                exit_code=-1,
                is_error=True,
            )

        try:
            # Execute the command via terminal (synchronous call)
            terminal_action = TerminalAction(command=action.command)
            terminal_obs = self.terminal_executor(terminal_action, conversation)

            return ReplayFrayObservation(
                content=[TextContent(text=terminal_obs.text)],
                command=action.command,
                exit_code=terminal_obs.metadata.exit_code,
                is_error=terminal_obs.metadata.exit_code != 0,
            )
        except Exception as e:
            return ReplayFrayObservation(
                content=[TextContent(text=f"Fray replay failed: {str(e)}")],
                command=action.command,
                exit_code=-1,
                is_error=True,
            )


RERUN_FRAY_DESCRIPTION = """Rerun Fray to verify that the concurrency bug has been fixed.

This tool runs a Fray command to explore thread interleavings and detect concurrency bugs.

IMPORTANT:
- You must rebuild the code (e.g., using javac or the build system) BEFORE calling this tool.
- Provide the full fray command to run.

Example usage for SCTBench:
- command: "fray -cp . Reorder3Bad"

Example usage for real-world projects:
- command: "fray -cp <full-classpath> org.pastalab.fray.helpers.JUnitRunner junit5 org.apache.kafka.streams.KafkaStreamsTest#shouldReturnFalse"

The tool will return whether the test passed (exit code 0, no bug) or failed (non-zero exit code, bug present).
"""


REPLAY_FRAY_DESCRIPTION = """Replay the last Fray recording to reproduce the bug with the current code.

When Fray detects a bug in exploration mode, it saves a recording to /tmp/report/recording.
This tool will replay the exact thread interleaving from that recording.

This is useful for:
- Adding debug print statements to understand the bug better
- Verifying that a specific interleaving no longer triggers the bug
- Iteratively debugging by adding prints, replaying, adding more prints, etc.

IMPORTANT:
- You must rebuild the code (e.g., using javac or the build system) BEFORE calling this tool.
- Provide the full fray command with the --replay flag.
- By default, replays from /tmp/report/recording (the last recording).

Example usage for SCTBench:
- command: "fray -cp . Reorder3Bad --replay /tmp/report/recording"

Example usage for real-world projects:
- command: "fray -cp <full-classpath> org.pastalab.fray.helpers.JUnitRunner junit5 org.apache.kafka.streams.KafkaStreamsTest#shouldReturnFalse --replay /tmp/report/recording"

The tool will return whether the replay passed (exit code 0) or failed (non-zero exit code, bug reproduced with failing stacktrace).
"""


class RerunFrayTool(ToolDefinition[RerunFrayAction, RerunFrayObservation]):
    """Tool for rerunning Fray tests."""

    @classmethod
    def create(
        cls,
        conv_state: "ConversationState",
        terminal_executor: TerminalExecutor,
        executor: ToolExecutor | None = None,
    ) -> Sequence["RerunFrayTool"]:
        """Create RerunFrayTool instance.

        Args:
            conv_state: Conversation state
            terminal_executor: Terminal executor for running commands
            executor: Optional custom executor

        Returns:
            Sequence containing the tool instance
        """
        if executor is None:
            executor = RerunFrayExecutor(terminal_executor)

        return [
            cls(
                name="rerun_fray",
                description=RERUN_FRAY_DESCRIPTION,
                action_type=RerunFrayAction,
                observation_type=RerunFrayObservation,
                executor=executor,
            )
        ]


class ReplayFrayTool(ToolDefinition[ReplayFrayAction, ReplayFrayObservation]):
    """Tool for replaying Fray recordings."""

    @classmethod
    def create(
        cls,
        conv_state: "ConversationState",
        terminal_executor: TerminalExecutor,
        executor: ToolExecutor | None = None,
    ) -> Sequence["ReplayFrayTool"]:
        """Create ReplayFrayTool instance.

        Args:
            conv_state: Conversation state
            terminal_executor: Terminal executor for running commands
            executor: Optional custom executor

        Returns:
            Sequence containing the tool instance
        """
        if executor is None:
            executor = ReplayFrayExecutor(terminal_executor)

        return [
            cls(
                name="replay_fray",
                description=REPLAY_FRAY_DESCRIPTION,
                action_type=ReplayFrayAction,
                observation_type=ReplayFrayObservation,
                executor=executor,
            )
        ]


# Factory function for registering both Fray tools together
def _make_fray_tools(conv_state: "ConversationState"):
    """Factory function to create both Fray tools with shared terminal executor.

    This function is registered with the tool registry and called by the SDK
    to instantiate the Fray tools.
    """
    from openhands.tools.terminal.impl import TerminalExecutor

    # Create shared terminal executor
    terminal_executor = TerminalExecutor(
        working_dir=str(conv_state.workspace.working_dir),
        username=None,
    )

    # Create and return both tools
    rerun_tool = RerunFrayTool.create(conv_state, terminal_executor)[0]
    replay_tool = ReplayFrayTool.create(conv_state, terminal_executor)[0]

    return [rerun_tool, replay_tool]


# Register the factory function (not the tool classes)
register_tool("FrayTools", _make_fray_tools)
