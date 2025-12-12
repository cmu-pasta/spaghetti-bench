# Agent Trace Visualizer

A web-based tool for visualizing and exploring agent execution traces from concurrency-bench.

## Features

- **Interactive Timeline**: View the complete sequence of events in agent conversations
- **Multiple Event Types**: Supports user messages, assistant messages, tool calls, tool results, and system prompts
- **Collapsible Sections**: Click any event to expand/collapse details
- **Patch Diff View**: View code changes with GitHub-style syntax highlighting
  - Separate tab for viewing the `.patch` file alongside each trace
  - Color-coded additions (green) and deletions (red)
  - File headers and metadata clearly displayed
- **Auto-Loading**: Automatically loads all traces from the results directory
- **Live Updates**: Watches for new or modified trace files and auto-reloads (polls every 2 seconds)
- **File Navigation**: Browse and switch between different trace files
- **Search**: Filter traces by name, task type, or category
- **Clean UI**: LangSmith-inspired interface for easy exploration

## Quick Start

### Option 1: Using the Python Server (Recommended)

The server automatically loads all traces from the `results/` directory:

```bash
cd viz
./serve_traces.py
# or
python3 serve_traces.py
```

Then open your browser to: http://localhost:8001

**What happens automatically:**
- All trace files from `../results/` are loaded on page load
- The page polls for changes every 2 seconds
- New trace files are automatically added to the list
- Updated trace files are automatically reloaded
- If you're viewing a trace that gets updated, it will be refreshed while preserving your position
- A green pulsing indicator shows the connection is active; it turns orange when loading

### Option 2: Standalone HTML File

Open `trace_visualizer.html` directly in your browser and manually upload JSON trace files using the file input.

## File Structure

```
viz/
├── README.md                # This file
├── trace_visualizer.html    # Standalone HTML visualizer
└── serve_traces.py          # Python HTTP server with auto-loading
```

## Trace File Format

The visualizer expects JSON files with the following structure:

```json
{
  "instance_id": "example_task",
  "task_type": "fix_bug",
  "model_id": "claude-sonnet-4-5",
  "description": "Task description",
  "benchmark_category": "sctbench",
  "success": true,
  "events": [
    {
      "kind": "MessageEvent",
      "timestamp": "2025-12-10T12:00:00",
      "source": "user",
      "llm_message": {
        "role": "user",
        "content": [{"type": "text", "text": "..."}]
      }
    }
    // ... more events
  ]
}
```

## Supported Event Types

The visualizer provides specialized rendering for each event type:

### ActionEvent (Agent Actions)
- **Terminal Commands**: Shows the command with syntax highlighting
- **File Editor Actions**:
  - `view`: Shows the path being viewed
  - `str_replace`: Shows old/new code side-by-side with diff-like formatting
  - `create`: Shows the file content being created
- **Reasoning**: Displays agent's reasoning/thinking in a highlighted box

### ObservationEvent (Tool Results)
- **Terminal Output**: Shows command output with exit codes and metadata
- **File Editor Results**: Shows the result of file operations
- **Error Highlighting**: Failed commands are shown with red background

### MessageEvent
- **User Messages**: User inputs and instructions
- **Assistant Messages**: Agent responses and explanations

### SystemPromptEvent
- System prompts sent to the agent (collapsed by default)

## Using the Visualizer

Once the server is running and you open http://localhost:8001:

1. **Timeline View** (default): See the full conversation flow
   - User messages and instructions
   - Agent reasoning and actions
   - Tool calls and results
   - Expandable/collapsible events

2. **Patch View**: Click the "📝 Patch" tab to see code changes
   - View the git diff of changes made by the agent
   - GitHub-style syntax highlighting
   - Green background for additions, red for deletions
   - If no patch file exists, you'll see a friendly message

3. **Shareable Links**: Click any trace to update the URL
   - The URL changes to include the trace path (e.g., `#trace/fix_bug/sctbench/Reorder3Bad.json`)
   - Copy and share the URL with others to link directly to that trace
   - Browser back/forward buttons work as expected

## Server API Endpoints

When using `serve_traces.py`:

- `GET /` - Serve the visualizer HTML
- `GET /api/traces` - List all available trace files
- `GET /api/trace/{path}` - Get a specific trace file
- `GET /api/patch/{path}` - Get the patch file for a trace

## Customization

You can modify the visualizer by editing `trace_visualizer.html`:

- **Styling**: Edit the `<style>` section
- **Behavior**: Modify the JavaScript in the `<script>` section
- **Event Rendering**: Update the `renderEvent()` function to customize how events are displayed

## Tips

- Click on event headers to expand/collapse event details
- Use the search box to filter traces by keywords
- Tool calls and results are syntax-highlighted for readability
- Large outputs are automatically made scrollable
