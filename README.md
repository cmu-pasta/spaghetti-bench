# Concurrency Bench

A benchmark for evaluating AI coding agents on concurrency bug tasks.

## Design

### Architecture

The benchmark consists of three main components:

1. **Tasks** (`src/concurrency_bench/tasks/`)
   - `FixBugTask`: Task for identifying and fixing concurrency bugs
   - `TriggerBugTask`: Task for writing code that reproduces concurrency bugs
   - Each task has `setup()` and `verify()` methods for task lifecycle management
   - Task loaders (e.g., `SCTBenchLoader`) handle building and running benchmark programs

2. **Agents** (`src/concurrency_bench/agents/`)
   - `FixBugAgent`: Agent specialized in fixing concurrency issues
   - `TriggerBugAgent`: Agent specialized in creating reproducible test cases for bugs
   - Built on [OpenHands Agent SDK](https://docs.openhands.dev/sdk/) with default tools (Terminal, FileEditor, TaskTracker)

3. **Runner** (`src/concurrency_bench/run_agent.py`)
   - Loads tasks from JSONL file
   - Creates isolated temporary workdir for each task
   - Initializes and runs the agent
   - Verifies results and reports summary
   - Saves full conversation data to results directory

### Workflow

```
Load Task → Create Temp Workdir → Copy Files → Initialize Agent → Run Agent → Verify → Save Results → Cleanup
```

## Setup

### Docker Setup (Recommended)

Build the Docker image using Nix flakes:

```bash
# Build the Docker image
nix build .#dockerImage

# Load into Docker
docker load < result
```

The Docker image includes:
- Python environment with all dependencies
- OpenJDK 25
- [Fray](https://github.com/cmu-pasta/fray) - JVM concurrency testing tool
- Standard Unix utilities (bash, grep, find, sed, awk, git, tmux, etc.)

### Local Setup

```bash
# Install dependencies (using uv)
uv sync

# Set API key
export LLM_API_KEY="your-api-key"
```

## Usage

### Quick Start (Docker)

Use the convenience script to run agents in Docker:

```bash
# Run bug fix task
./run_agent.sh fix

# Run bug trigger task
./run_agent.sh trigger
```

The script:
- Mounts the current directory to `/workspace` in the container
- Reads API key from `~/.aws/bedrock.key`
- Runs all tasks in `src/concurrency_bench/sctbench.jsonl`
- Saves results to `results/` directory

### Manual Usage (Docker)

```bash
docker run --rm -it \
  -v $(pwd):/workspace \
  -e LLM_API_KEY="your-api-key" \
  concurrency-bench:latest \
  python src/concurrency_bench/run_agent.py \
    --tasks-file src/concurrency_bench/sctbench.jsonl \
    --task-type fix_bug \
    --model-id bedrock/global.anthropic.claude-sonnet-4-5-20250929-v1:0 \
    --results-dir results
```

### Local Usage (without Docker)

```bash
uv run python src/concurrency_bench/run_agent.py \
  --tasks-file src/concurrency_bench/sctbench.jsonl \
  --task-type fix_bug \
  --model-id bedrock/global.anthropic.claude-sonnet-4-5-20250929-v1:0
```

### Run Single Task

```bash
./run_agent.sh fix  # or use docker/uv run commands with:
# --instance-id Reorder3Bad
```

## Task File Format

Tasks are defined in JSONL format (one JSON object per line):

```jsonl
{"instance_id": "Reorder3Bad", "path": "benchmarks/SCTBench/cs/origin/Reorder3Bad.java", "description": "Memory ordering bug with concurrent reads and writes to volatile variables", "benchmark_category": "sctbench", "subcategory": "cs/origin", "loader": "SCTBenchLoader"}
```

**Fields:**
- `instance_id`: Unique task identifier
- `path`: Path to file/directory (relative to `--base-path`)
- `description`: Description of the concurrency bug
- `benchmark_category`: Category of the benchmark (e.g., "sctbench")
- `subcategory`: Subcategory within the benchmark (e.g., "cs/origin")
- `loader`: Task loader class name (e.g., "SCTBenchLoader") - handles building and running the task

## Command-Line Options

| Option | Required | Description |
|--------|----------|-------------|
| `--tasks-file` | Yes | Path to JSONL file containing tasks |
| `--task-type` | Yes | Task type: `fix_bug` or `trigger_bug` |
| `--model-id` | Yes | Model ID (e.g., `bedrock/global.anthropic.claude-sonnet-4-5-20250929-v1:0`) |
| `--base-path` | No | Base path for resolving task paths (default: current directory) |
| `--api-key` | No | LLM API key (default: `LLM_API_KEY` env var) |
| `--instance-id` | No | Run only the specified task |
| `--results-dir` | No | Directory to save conversation results (default: `results/`) |

## Output

### Console Output

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
Model: bedrock/global.anthropic.claude-sonnet-4-5-20250929-v1:0
================================================================================

Created workdir: /tmp/concurrency_bench_Reorder3Bad_abc123/
Copied benchmarks/SCTBench/cs/origin/Reorder3Bad.java -> /tmp/concurrency_bench_Reorder3Bad_abc123/
Starting agent...
...
Agent finished!

Verifying results...
Success: True
Saved conversation to: results/fix_bug/sctbench/Reorder3Bad.json
```

### Results Directory

Conversation data is saved in a structured directory:

```
results/
├── fix_bug/
│   └── sctbench/
│       └── Reorder3Bad.json
└── trigger_bug/
    └── sctbench/
        └── Reorder3Bad.json
```

Each JSON file contains:
- `instance_id` - Task identifier
- `task_type` - "fix_bug" or "trigger_bug"
- `model_id` - Model used for the task
- `description` - Task description
- `benchmark_category` - Benchmark category
- `subcategory` - Benchmark subcategory
- `conversation_id` - Unique conversation ID
- `success` - Boolean indicating task success
- `events` - Full conversation event stream (all messages, tool calls, responses, etc.)

This data enables post-hoc analysis, debugging, and replay of agent interactions.

## Benchmarks

### SCTBench

The repository includes benchmarks from [SCTBench](https://github.com/mc-imperial/sctbench), a suite of concurrency bugs translated to Java. These are located in `benchmarks/SCTBench/` and include:

- **cs/origin/** - Original concurrency bugs (data races, atomicity violations, etc.)
- **cs/hard/** - More challenging variants with increased thread counts
- **cb/** - Concurrent data structure bugs
- **chess/** - Work-stealing queue bugs

All SCTBench tasks use the `SCTBenchLoader` which:
1. Compiles Java files with `javac`
2. Runs with `java -ea` (assertions enabled)
3. Reports success based on exit code

### Available Tools

Agents have access to standard development tools in the Docker environment:

- **Java**: OpenJDK 25 for compiling and running benchmarks
- **Fray**: Concurrency testing tool for exploring thread interleavings (available as `/bin/fray`)
- **Standard utilities**: bash, grep, find, sed, awk, git, tmux

Example Fray usage:
```bash
javac MyBuggyProgram.java
fray -cp . MyBuggyProgram --iter 10000
```

## Development

### Modifying the Docker Image

The Docker image is built from `flake.nix`. After making changes:

```bash
nix build .#dockerImage
docker load < result
```

Note: Python code changes do NOT require rebuilding - the `run_agent.sh` script mounts your local directory, so edits are immediately visible.

### Adding New Benchmarks

1. Add benchmark files to `benchmarks/`
2. Create a task loader in `src/concurrency_bench/tasks/loaders/`
3. Add task entries to a JSONL file with the appropriate loader
4. Run with `--tasks-file your_tasks.jsonl`
