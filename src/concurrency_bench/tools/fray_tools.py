"""Fray-specific tools for debugging concurrency bugs."""

from collections.abc import Sequence
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
    stdout: str = Field(default="", description="Standard output from the command")
    stderr: str = Field(default="", description="Standard error from the command")

    @property
    def to_llm_content(self) -> Sequence[TextContent | ImageContent]:
        llm_content: list[TextContent | ImageContent] = []

        if self.is_error:
            llm_content.append(TextContent(text=self.ERROR_MESSAGE_HEADER))

        result = f"Command: {self.command}\n\n"

        if self.exit_code == 0:
            result += "✅ Test PASSED - No concurrency bug detected\n\n"
            if self.stdout:
                result += f"=== STDOUT ===\n{self.stdout}\n\n"
            if self.stderr:
                result += f"=== STDERR ===\n{self.stderr}\n\n"
        else:
            result += "❌ Test FAILED - Concurrency bug still present\n\n"
            # Always include stdout/stderr on failure for debugging
            result += f"=== STDOUT ===\n{self.stdout or '(empty)'}\n\n"
            result += f"=== STDERR ===\n{self.stderr or '(empty)'}\n\n"

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

            # Extract stdout and stderr from terminal observation metadata
            stdout = getattr(terminal_obs.metadata, 'stdout', '') or ''
            stderr = getattr(terminal_obs.metadata, 'stderr', '') or ''

            # Fall back to text if stdout/stderr not available separately
            if not stdout and not stderr:
                stdout = terminal_obs.text

            return RerunFrayObservation(
                content=[TextContent(text=terminal_obs.text)],
                command=action.command,
                exit_code=terminal_obs.metadata.exit_code,
                stdout=stdout,
                stderr=stderr,
                is_error=terminal_obs.metadata.exit_code != 0,
            )
        except Exception as e:
            return RerunFrayObservation(
                content=[TextContent(text=f"Fray execution failed: {str(e)}")],
                command=action.command,
                exit_code=-1,
                stdout="",
                stderr=str(e),
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


# Factory function for registering Fray tools
def _make_fray_tools(conv_state: "ConversationState"):
    """Factory function to create Fray tools with terminal executor.

    This function is registered with the tool registry and called by the SDK
    to instantiate the Fray tools.
    """
    from openhands.tools.terminal.impl import TerminalExecutor

    # Create terminal executor
    terminal_executor = TerminalExecutor(
        working_dir=str(conv_state.workspace.working_dir),
        username=None,
    )

    # Create and return the rerun tool
    rerun_tool = RerunFrayTool.create(conv_state, terminal_executor)[0]

    return [rerun_tool]


# Register the factory function (not the tool classes)
register_tool("FrayTools", _make_fray_tools)
