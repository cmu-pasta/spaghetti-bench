#!/bin/bash

# Default values
MAX_WORKERS=1
MEMORY="8g"
CPUS="4"
ENABLE_FRAY_TOOLS=""
REPS=1

# Parse arguments
if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <fix|trigger|gold> [--max-workers N] [--memory XG] [--cpus N] [--enable-fray-tools] [--reps N]"
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
    --reps)
      REPS="$2"
      shift 2
      ;;
    *)
      echo "Unknown parameter: $1"
      exit 1
      ;;
  esac
done

# Array to store background PIDs
PIDS=()

for REP in $(seq 1 $REPS); do
  echo "=========================================="
  echo "Starting repetition $REP of $REPS"
  echo "=========================================="

  # Only pass --repetition if running multiple reps
  if [ "$REPS" -gt 1 ]; then
    REP_ARG="--repetition $REP"
  else
    REP_ARG=""
  fi

  docker run --rm \
    --memory="$MEMORY" \
    --cpus="$CPUS" \
    -v $(pwd):/workspace \
    -e LLM_API_KEY=$(cat ~/.aws/bedrock.key) \
    concurrency-bench:latest \
    python src/concurrency_bench/run_agent.py \
      --tasks-file src/concurrency_bench/sctbench.jsonl \
      --task-type "$TASK_TYPE" \
      --model-id bedrock/global.anthropic.claude-opus-4-5-20251101-v1:0 \
      --results-dir results/claude-opus-4-5/ \
      --max-workers "$MAX_WORKERS" \
      $ENABLE_FRAY_TOOLS \
      $REP_ARG &

  PIDS+=($!)
done

echo "=========================================="
echo "Waiting for all $REPS repetitions to complete..."
echo "=========================================="

# Wait for all background processes and track failures
FAILED=0
for PID in "${PIDS[@]}"; do
  if ! wait $PID; then
    FAILED=$((FAILED + 1))
  fi
done

echo "=========================================="
echo "All repetitions completed. Failed: $FAILED / $REPS"
echo "=========================================="

exit $FAILED

