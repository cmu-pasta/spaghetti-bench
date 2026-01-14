#!/usr/bin/env python3
"""Script to run concurrency benchmark agents on tasks."""

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from concurrency_bench.agents import FixBugAgent, TriggerBugAgent
from concurrency_bench.agents.builtin_agents import GoldenAgent
from concurrency_bench.task_config import TaskConfig
from concurrency_bench.tasks import loaders
from concurrency_bench.tasks.fix_bug import FixBugTask
from concurrency_bench.tasks.trigger_bug import TriggerBugTask


def load_tasks(tasks_file: Path) -> list[TaskConfig]:
    """Load tasks from a JSONL file.

    Args:
        tasks_file: Path to the JSONL file.

    Returns:
        List of Task objects.
    """
    tasks = []
    with open(tasks_file) as f:
        for line in f:
            line = line.strip()
            if line:
                task_dict = json.loads(line)
                tasks.append(TaskConfig.from_dict(task_dict))
    return tasks


def setup_workdir(task: TaskConfig, base_path: Path) -> Path:
    """Create a temporary directory and copy the task files or clone repository.

    Args:
        task: Task object with path or repo_url/commit fields.
        base_path: Base path to resolve relative paths from.

    Returns:
        Path to the temporary working directory.
    """
    # Create temporary directory
    temp_dir = Path(
        tempfile.mkdtemp(
            prefix=f"concurrency_bench_{task.instance_id}_",
            dir=base_path / "workspaces",
        )
    )

    print(f"Created workdir: {temp_dir}")

    # For real-world tasks with repo_url, the loader will handle cloning
    if task.repo_url is not None:
        print(f"Repository will be cloned by loader into: {temp_dir}/repo")
        return temp_dir

    # For SCTBench-style tasks, copy the file
    if task.path is None:
        raise ValueError(f"Task {task.instance_id} has neither repo_url nor path")

    source_path = base_path / task.path

    if not source_path.exists():
        raise FileNotFoundError(f"Source path does not exist: {source_path}")

    # Copy the path recursively
    if source_path.is_dir():
        dest_path = temp_dir / source_path.name
        shutil.copytree(source_path, dest_path)
    else:
        dest_path = temp_dir / source_path.name
        shutil.copy2(source_path, dest_path)

    print(f"Copied {source_path} -> {temp_dir}")

    return temp_dir


def run_task(
    task_config: TaskConfig,
    task_type: str,
    model_id: str,
    base_path: Path,
    results_dir: Path,
    api_key: str | None = None,
    enable_fray_tools: bool = False,
    keep_result: bool = False,
):
    """Run a single task with the specified agent.

    Args:
        task: Task object from JSONL.
        task_type: Type of task ('fix_bug' or 'trigger_bug').
        model_id: Model ID to use for the agent.
        base_path: Base path to resolve relative paths from.
        results_dir: Directory to save conversation results.
        api_key: Optional API key for the LLM.
        enable_fray_tools: Enable Fray-specific debugging tools for fix_bug tasks.
    """
    print(f"\n{'=' * 80}")
    print(f"Running task: {task_config.instance_id}")
    print(f"Description: {task_config.description}")
    print(f"Task type: {task_type}")
    print(f"Model: {model_id}")
    print(f"{'=' * 80}\n")

    # Setup workdir
    workdir = setup_workdir(task_config, base_path)

    # Initialize task loader based on task.loader field
    loader_name = task_config.loader
    if loader_name:
        loader_class = getattr(loaders, loader_name, None)
        if loader_class is None:
            raise ValueError(f"Unknown loader: {loader_name}")

        # Real-world loaders (Kafka, Lucene, Guava) need additional parameters
        if loader_name in [
            "KafkaLoader",
            "LuceneLoader",
            "GuavaLoader",
            "UniffleLoader",
            "MercuryLoader",
        ]:
            task_loader = loader_class(
                task_name=task_config.instance_id,
                repo_url=task_config.repo_url,
                commit=task_config.commit,
                test_class=task_config.test_class,
                test_method=task_config.test_method,
                fray_args=task_config.fray_args,
            )
        else:
            # SCTBench and other simple loaders
            task_loader = loader_class(task_name=task_config.instance_id)
    else:
        task_loader = None

    try:
        # Initialize task
        if task_type == "fix_bug":
            task_obj = FixBugTask(workdir=workdir, loader=task_loader)

            # Setup the task to get the stack trace
            print("Setting up task...")
            setup_output = task_obj.setup()
            print("Setup complete!")

            agent = FixBugAgent(
                workdir=workdir,
                model_id=model_id,
                api_key=api_key,
                task_config=task_config,
                task_instance=task_obj,
                enable_fray_tools=enable_fray_tools,
            )
        elif task_type == "trigger_bug":
            # FIXME: This part is broken rn
            task_obj = TriggerBugTask(workdir=workdir, loader=task_loader)

            # Setup the task for trigger_bug
            print("Setting up task...")
            setup_output = task_obj.setup()
            print("Setup complete!")

            agent = TriggerBugAgent(
                workdir=workdir,
                model_id=model_id,
                api_key=api_key,
                task_info=task_info,
            )
        elif task_type == "run_gold":
            # Golden agent: apply patch from URL
            if task_config.patch_url is None:
                raise ValueError(f"Task {task_config.instance_id} has no patch_url for run_gold task type")

            task_obj = FixBugTask(workdir=workdir, loader=task_loader)

            # Setup the task (clone repo, build)
            print("Setting up task...")
            setup_output = task_obj.setup()
            print("Setup complete!")

            # Apply the golden patch
            agent = GoldenAgent()
            print(f"Applying golden patch from: {task_config.patch_url}")
            conversation = agent.run(workdir=workdir, patch_url=task_config.patch_url)
            print("Golden patch applied!")

            # Skip the normal agent run since GoldenAgent doesn't use the SDK
            # Jump directly to verification after creating git baseline
        else:
            raise ValueError(f"Unknown task type: {task_type}")

        # Create a git baseline after setup, before the agent runs
        git_dir = workdir / "repo" if (workdir / "repo").exists() else workdir
        subprocess.run(["git", "init"], cwd=git_dir, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "Concurrency Bench"],
            cwd=git_dir,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "bench@example.com"],
            cwd=git_dir,
            capture_output=True,
        )
        subprocess.run(["git", "add", "-A"], cwd=git_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Baseline after setup"],
            cwd=git_dir,
            capture_output=True,
        )

        # Run the agent (unless it's run_gold which already ran)
        if task_type != "run_gold":
            print("Starting agent...")
            conversation = agent.run_agent()
            print("\nAgent finished!")

        # Verify the result
        print("\nVerifying results...")
        result = task_obj.verify()
        print(f"Success: {result.success}")

        # Save conversation data
        conversation_data = {
            "instance_id": task_config.instance_id,
            "task_type": task_type,
            "model_id": model_id,
            "description": task_config.description,
            "benchmark_category": task_config.benchmark_category,
            "subcategory": task_config.subcategory,
            "conversation_id": str(conversation.id),
            "success": result.success,
            "setup_output": setup_output,
            "verify_output": result.verify_output,
            "events": [event.model_dump() for event in conversation.state.events],
        }

        # Sanitize model_id for use in directory name (replace / with _)
        sanitized_model_id = model_id.replace("/", "_").replace(":", "_")

        # Add with_fray or without_fray based on enable_fray_tools flag
        fray_mode = "with_fray" if enable_fray_tools else "without_fray"

        # Write to results directory with structure: results_dir/model_id/fray_mode/task_type/benchmark_category/instance_id.json
        task_results_dir = results_dir / sanitized_model_id / fray_mode / task_type / task_config.benchmark_category
        task_results_dir.mkdir(parents=True, exist_ok=True)
        result_file = task_results_dir / f"{task_config.instance_id}.json"
        with open(result_file, "w") as f:
            json.dump(conversation_data, f, indent=2)
        print(f"Saved conversation to: {result_file}")

        # Save git diff of changes made by the agent
        git_dir = workdir / "repo" if (workdir / "repo").exists() else workdir
        subprocess.run(["git", "add", "-A"], cwd=git_dir, capture_output=True)

        # Generate diff against baseline commit
        diff_result = subprocess.run(
            ["git", "diff", "--cached"],
            cwd=git_dir,
            capture_output=True,
            text=True,
        )

        patch_file = task_results_dir / f"{task_config.instance_id}.patch"
        with open(patch_file, "w") as f:
            f.write(diff_result.stdout)
        print(f"Saved patch to: {patch_file}")

        return result

    finally:
        # Cleanup temporary directory
        if not keep_result and workdir.exists():
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
        choices=["fix_bug", "trigger_bug", "run_gold"],
        help="Type of task to run",
    )
    parser.add_argument(
        "--model-id",
        type=str,
        required=False,
        default="golden",
        help="Model ID to use (e.g., 'anthropic/claude-sonnet-4-5-20250929'). Defaults to 'golden' for run_gold task type.",
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
    parser.add_argument(
        "--max-workers",
        type=int,
        default=1,
        help="Maximum number of parallel workers (default: 1)",
    )
    parser.add_argument(
        "--enable-fray-tools",
        action="store_true",
        help="Enable Fray-specific debugging tools (rerun_fray, replay_fray) for fix_bug tasks",
    )
    parser.add_argument(
        "--keep-result",
        action="store_true",
        help="Keep result files even if the task fails",
    )

    args = parser.parse_args()

    # Load tasks
    print(f"Loading tasks from: {args.tasks_file}")
    tasks = load_tasks(args.tasks_file)
    print(f"Loaded {len(tasks)} task(s)")

    # Filter by instance_id if specified
    if args.instance_id:
        tasks = [t for t in tasks if t.instance_id == args.instance_id]
        if not tasks:
            print(f"Error: No task found with instance_id '{args.instance_id}'")
            return 1
        print(f"Running single task: {args.instance_id}")

    # Run tasks
    results = []

    if args.max_workers == 1:
        # Sequential execution
        print("Running tasks sequentially")
        for task in tasks:
            try:
                result = run_task(
                    task_config=task,
                    task_type=args.task_type,
                    model_id=args.model_id,
                    base_path=args.base_path,
                    results_dir=args.results_dir,
                    api_key=args.api_key,
                    enable_fray_tools=args.enable_fray_tools,
                    keep_result=args.keep_result,
                )
                results.append(
                    {
                        "instance_id": task.instance_id,
                        "success": result.success,
                    }
                )
                print(f"Completed: {task.instance_id} - Success: {result.success}")
            except Exception as e:
                tb = traceback.format_exc()
                print(tb)
                print(f"Error running task {task.instance_id}: {e}")
                results.append(
                    {
                        "instance_id": task.instance_id,
                        "success": False,
                        "error": str(e),
                    }
                )
    else:
        # Parallel execution
        print(f"Running tasks in parallel with {args.max_workers} workers")
        with ProcessPoolExecutor(max_workers=args.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(
                    run_task,
                    task=task,
                    task_type=args.task_type,
                    model_id=args.model_id,
                    base_path=args.base_path,
                    results_dir=args.results_dir,
                    api_key=args.api_key,
                    enable_fray_tools=args.enable_fray_tools,
                ): task
                for task in tasks
            }

            # Process results as they complete
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append(
                        {
                            "instance_id": task.instance_id,
                            "success": result.success,
                        }
                    )
                    print(f"Completed: {task.instance_id} - Success: {result.success}")
                except Exception as e:
                    tb = traceback.format_exc()
                    print(tb)
                    print(f"Error running task {task.instance_id}: {e}")
                    results.append(
                        {
                            "instance_id": task.instance_id,
                            "success": False,
                            "error": str(e),
                        }
                    )

    # Print summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    successful = sum(1 for r in results if r["success"])
    print(f"Total tasks: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")

    return 0 if successful == len(results) else 1


if __name__ == "__main__":
    exit(main())
