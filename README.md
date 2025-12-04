# Concurrency Bench

A benchmark for evaluating AI coding agents on concurrency bug tasks.

## Design

### Architecture

The benchmark consists of three main components:

1. **Tasks** (`src/concurrency_bench/tasks/`)
   - `FixBugTask`: Task for identifying and fixing concurrency bugs
   - `TriggerBugTask`: Task for writing code that reproduces concurrency bugs
   - Each task has `setup()` and `verify()` methods, which are currently not implemented.

2. **Agents** (`src/concurrency_bench/agents/`)
   - `FixBugAgent`: Agent specialized in fixing concurrency issues
   - `TriggerBugAgent`: Agent specialized in creating reproducible test cases for bugs
   - Built on [OpenHands Agent SDK](https://docs.openhands.dev/sdk/) with default tools (Terminal, FileEditor, TaskTracker)

3. **Runner** (`src/concurrency_bench/run_agent.py`)
   - Loads tasks from JSONL file
   - Creates isolated temporary workdir for each task
   - Initializes and runs the agent
   - Verifies results and reports summary

### Workflow

```
Load Task → Create Temp Workdir → Copy Files → Initialize Agent → Run Agent → Verify → Cleanup
```

## Setup

```bash
# Install dependencies (using uv)
uv sync

# Set API key
export LLM_API_KEY="your-api-key"
```

## Usage

### Basic Usage

```bash
cd src/concurrency_bench
uv run python src/concurrency_bench/run_agent.py \
  --tasks-file src/concurrency_bench/example.jsonl \
  --task-type fix_bug \
  --model-id bedrock/global.anthropic.claude-sonnet-4-5-20250929-v1:0
```

### Run Single Task

```bash
cd src/concurrency_bench
uv run python run_agent.py \
  --tasks-file example.jsonl \
  --task-type trigger_bug \
  --model-id bedrock/global.anthropic.claude-sonnet-4-5-20250929-v1:0 \
  --instance-id Reorder3Bad
```

## Task File Format

Tasks are defined in JSONL format (one JSON object per line):

```jsonl
{"instance_id": "Reorder3Bad", "path": "bms/SCTBench/cs/origin/Reorder3Bad.java", "description": "Memory ordering bug with concurrent reads and writes to volatile variables", "benchmark_category": "sctbench", "subcategory": "cs/origin"}
```

**Fields:**
- `instance_id`: Unique task identifier
- `path`: Path to file/directory (relative to `--base-path`)
- `description`: Description of the concurrency bug
- `benchmark_category`: Category of the benchmark
- `subcategory`: Subcategory within the benchmark

## Command-Line Options

| Option | Required | Description |
|--------|----------|-------------|
| `--tasks-file` | Yes | Path to JSONL file containing tasks |
| `--task-type` | Yes | Task type: `fix_bug` or `trigger_bug` |
| `--model-id` | Yes | Model ID (e.g., `anthropic/claude-sonnet-4-5-20250929`) |
| `--base-path` | No | Base path for resolving task paths (default: current directory) |
| `--api-key` | No | LLM API key (default: `LLM_API_KEY` env var) |
| `--base-url` | No | LLM base URL (default: `LLM_BASE_URL` env var) |
| `--instance-id` | No | Run only the specified task |

## Output

The runner prints:
- Task information and progress
- Agent execution output
- Verification results
- Summary with success/failure counts

Example output:
```
================================================================================
Running task: Reorder3Bad
Description: Memory ordering bug with concurrent reads and writes to volatile variables
Task type: fix_bug
Model: anthropic/claude-sonnet-4-5-20250929
================================================================================

Created workdir: /tmp/concurrency_bench_Reorder3Bad_abc123/
Copied bms/SCTBench/cs/origin/Reorder3Bad.java -> /tmp/concurrency_bench_Reorder3Bad_abc123/
Starting agent...
...
Agent finished!

Verifying results...
Success: True
```
