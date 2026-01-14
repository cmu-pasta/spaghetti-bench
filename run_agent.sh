#!/bin/bash

# Default values
MAX_WORKERS=1
MEMORY="8g"
CPUS="4"
ENABLE_FRAY_TOOLS=""

# Parse arguments
if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <fix|trigger|gold> [--max-workers N] [--memory XG] [--cpus N] [--enable-fray-tools]"
  exit 1
fi

case "$1" in
  fix)
    TASK_TYPE="fix_bug"
    ;;
  trigger)
    TASK_TYPE="trigger_bug"
    ;;
  gold)
    TASK_TYPE="run_gold"
    ;;
  *)
    echo "Error: Invalid argument '$1'. Must be 'fix', 'trigger', or 'gold'."
    exit 1
    ;;
esac
shift

# Parse optional arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --max-workers)
      MAX_WORKERS="$2"
      shift 2
      ;;
    --memory)
      MEMORY="$2"
      shift 2
      ;;
    --cpus)
      CPUS="$2"
      shift 2
      ;;
    --enable-fray-tools)
      ENABLE_FRAY_TOOLS="--enable-fray-tools"
      shift
      ;;
    *)
      echo "Unknown parameter: $1"
      exit 1
      ;;
  esac
done

docker run --rm -it \
  --memory="$MEMORY" \
  --cpus="$CPUS" \
  -v $(pwd):/workspace \
  -e LLM_API_KEY=$(cat ~/.aws/bedrock.key) \
  concurrency-bench:latest \
  python src/concurrency_bench/run_agent.py \
    --tasks-file src/concurrency_bench/kafka.jsonl \
    --task-type "$TASK_TYPE" \
    --model-id bedrock/global.anthropic.claude-opus-4-5-20251101-v1:0 \
    --results-dir results/claude-sonnet-4-5/ \
    --max-workers "$MAX_WORKERS" \
    $ENABLE_FRAY_TOOLS

