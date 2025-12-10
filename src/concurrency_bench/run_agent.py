#!/usr/bin/env python3
"""Script to run concurrency benchmark agents on tasks."""

import os
import argparse
import json
import shutil
import tempfile
from pathlib import Path
import traceback

from concurrency_bench.agents import FixBugAgent, TriggerBugAgent
from concurrency_bench.tasks.fix_bug import FixBugTask
from concurrency_bench.tasks.trigger_bug import TriggerBugTask
from concurrency_bench.tasks import loaders


def load_tasks(tasks_file: Path) -> list[dict]:
    """Load tasks from a JSONL file.

    Args:
        tasks_file: Path to the JSONL file.

    Returns:
        List of task dictionaries.
    """
    tasks = []
    with open(tasks_file) as f:
        for line in f:
            line = line.strip()
            if line:
                tasks.append(json.loads(line))
    return tasks


def setup_workdir(task: dict, base_path: Path) -> Path:
    """Create a temporary directory and copy the task files.

    Args:
        task: Task dictionary with 'path' field.
        base_path: Base path to resolve relative paths from.

    Returns:
        Path to the temporary working directory.
    """
    # Create temporary directory
    temp_dir = Path(
        tempfile.mkdtemp(
            prefix=f"concurrency_bench_{task['instance_id']}_",
            dir=base_path / "workspaces",
        )
    )

    # Resolve the source path
    source_path = base_path / task["path"]

    if not source_path.exists():
        raise FileNotFoundError(f"Source path does not exist: {source_path}")

    # Copy the path recursively
    if source_path.is_dir():
        dest_path = temp_dir / source_path.name
        shutil.copytree(source_path, dest_path)
    else:
        dest_path = temp_dir / source_path.name
        shutil.copy2(source_path, dest_path)

    print(f"Created workdir: {temp_dir}")
    print(f"Copied {source_path} -> {temp_dir}")

    return temp_dir


def run_task(
    task: dict,
    task_type: str,
    model_id: str,
    base_path: Path,
    results_dir: Path,
    api_key: str | None = None,
):
    """Run a single task with the specified agent.

    Args:
        task: Task dictionary from JSONL.
        task_type: Type of task ('fix_bug' or 'trigger_bug').
        model_id: Model ID to use for the agent.
        base_path: Base path to resolve relative paths from.
        results_dir: Directory to save conversation results.
        api_key: Optional API key for the LLM.
    """
    print(f"\n{'='*80}")
    print(f"Running task: {task['instance_id']}")
    print(f"Description: {task['description']}")
    print(f"Task type: {task_type}")
    print(f"Model: {model_id}")
    print(f"{'='*80}\n")

    # Setup workdir
    workdir = setup_workdir(task, base_path)

    # Initialize task loader based on task["loader"] field
    loader_name = task.get("loader")
    if loader_name:
        loader_class = getattr(loaders, loader_name, None)
        if loader_class is None:
            raise ValueError(f"Unknown loader: {loader_name}")
        task_loader = loader_class(task_name=task.get("task_name", task["instance_id"]))
    else:
        task_loader = None

    try:
        # Initialize task
        if task_type == "fix_bug":
            task_obj = FixBugTask(workdir=workdir, loader=task_loader)
            agent = FixBugAgent(
                workdir=workdir,
                model_id=model_id,
                api_key=api_key,
            )
        elif task_type == "trigger_bug":
            task_obj = TriggerBugTask(workdir=workdir, loader=task_loader)
            agent = TriggerBugAgent(
                workdir=workdir,
                model_id=model_id,
                api_key=api_key,
            )
        else:
            raise ValueError(f"Unknown task type: {task_type}")

        # Setup the task
        print("Setting up task...")
        setup_output = task_obj.setup()
        print("Setup complete!")

        # Run the agent
        print("Starting agent...")
        conversation = agent.run_agent()
        print("\nAgent finished!")

        # Verify the result
        print("\nVerifying results...")
        result = task_obj.verify()
        print(f"Success: {result.success}")

        # Save conversation data
        conversation_data = {
            "instance_id": task["instance_id"],
            "task_type": task_type,
            "model_id": model_id,
            "description": task.get("description", ""),
            "benchmark_category": task.get("benchmark_category", ""),
            "subcategory": task.get("subcategory", ""),
            "conversation_id": str(conversation.id),
            "success": result.success,
            "setup_output": setup_output,
            "verify_output": result.verify_output,
            "events": [event.model_dump() for event in conversation.state.events],
        }

        # Write to results directory with structure: results_dir/task_type/benchmark_category/instance_id.json
        task_results_dir = results_dir / task_type / task.get("benchmark_category", "unknown")
        task_results_dir.mkdir(parents=True, exist_ok=True)
        result_file = task_results_dir / f"{task['instance_id']}.json"
        with open(result_file, "w") as f:
            json.dump(conversation_data, f, indent=2)
        print(f"Saved conversation to: {result_file}")

        return result

    finally:
        # Cleanup temporary directory
        print(f"\nCleaning up workdir: {workdir}")
        shutil.rmtree(workdir, ignore_errors=True)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Run concurrency benchmark agents on tasks"
    )
    parser.add_argument(
        "--tasks-file",
        type=Path,
        required=True,
        help="Path to JSONL file containing tasks",
    )
    parser.add_argument(
        "--task-type",
        type=str,
        required=True,
        choices=["fix_bug", "trigger_bug"],
        help="Type of task to run",
    )
    parser.add_argument(
        "--model-id",
        type=str,
        required=True,
        help="Model ID to use (e.g., 'anthropic/claude-sonnet-4-5-20250929')",
    )
    parser.add_argument(
        "--base-path",
        type=Path,
        default=Path.cwd(),
        help="Base path to resolve relative paths from (default: current directory)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="API key for the LLM provider (defaults to LLM_API_KEY env var)",
    )
    parser.add_argument(
        "--instance-id",
        type=str,
        help="Run only the task with this instance_id",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("results"),
        help="Directory to save conversation results (default: results/)",
    )

    args = parser.parse_args()

    # Load tasks
    print(f"Loading tasks from: {args.tasks_file}")
    tasks = load_tasks(args.tasks_file)
    print(f"Loaded {len(tasks)} task(s)")

    # Filter by instance_id if specified
    if args.instance_id:
        tasks = [t for t in tasks if t["instance_id"] == args.instance_id]
        if not tasks:
            print(f"Error: No task found with instance_id '{args.instance_id}'")
            return 1
        print(f"Running single task: {args.instance_id}")

    # Run tasks
    results = []
    for task in tasks:
        try:
            result = run_task(
                task=task,
                task_type=args.task_type,
                model_id=args.model_id,
                base_path=args.base_path,
                results_dir=args.results_dir,
                api_key=args.api_key,
            )
            results.append(
                {
                    "instance_id": task["instance_id"],
                    "success": result.success,
                }
            )
        except Exception as e:
            tb = traceback.format_exc()
            print(tb)
            print(f"Error running task {task['instance_id']}: {e}")
            results.append(
                {
                    "instance_id": task["instance_id"],
                    "success": False,
                    "error": str(e),
                }
            )

    # Print summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    successful = sum(1 for r in results if r["success"])
    print(f"Total tasks: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")

    return 0 if successful == len(results) else 1


if __name__ == "__main__":
    exit(main())
