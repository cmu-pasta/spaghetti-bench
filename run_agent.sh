#!/bin/bash

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <fix|trigger>"
  exit 1
fi

case "$1" in
  fix)
    TASK_TYPE="fix_bug"
    ;;
  trigger)
    TASK_TYPE="trigger_bug"
    ;;
  *)
    echo "Error: Invalid argument '$1'. Must be 'fix' or 'trigger'."
    exit 1
    ;;
esac

docker run --rm -it \
  -v $(pwd):/workspace \
  -e LLM_API_KEY=$(cat ~/.aws/bedrock.key) \
  concurrency-bench:latest \
  python src/concurrency_bench/run_agent.py \
    --tasks-file src/concurrency_bench/sctbench.jsonl \
    --task-type "$TASK_TYPE" \
    --model-id bedrock/global.anthropic.claude-sonnet-4-5-20250929-v1:0 \
    --results-dir results

