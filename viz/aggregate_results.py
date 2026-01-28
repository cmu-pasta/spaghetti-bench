#!/usr/bin/env python3
"""
Aggregate benchmark results from all trace files.
Creates a summary JSON file with per-model and per-category statistics.
Averages results over 5 repetitions per model+config combination.
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone


def get_friendly_name(model_id):
    """Convert model ID to friendly name."""
    mapping = {
        "bedrock_global.anthropic.claude-sonnet-4-5-20250929-v1_0": "Claude 4.5 Sonnet",
        "bedrock_global.anthropic.claude-opus-4-5-20251101-v1_0": "Claude 4.5 Opus",
        "openai_gpt-5.2": "GPT-5.2",
        "openai_gpt-5.1-codex": "GPT-5.2 Codex",
        "gemini_gemini-3-pro-preview": "Gemini 3.0 Pro",
        "gemini_gemini-3-flash-preview": "Gemini 3.0 Flash",
        "bedrock_qwen.qwen3-coder-480b-a35b-v1_0": "Qwen 3 Coder",
        "openai_gpt-4o": "GPT-4o",
        "bedrock_us.meta.llama4-maverick-17b-instruct-v1_0": "Llama 4 Maverick 17B",
    }
    return mapping.get(model_id, model_id)


def aggregate_results(results_dir: Path, output_file: Path):
    """Aggregate all trace results into a summary JSON file."""

    # Data structures for aggregation
    # Key: (model_id, config) -> instance_id -> [list of success values across reps]
    instance_results = defaultdict(lambda: defaultdict(list))

    # Store metadata for each model+config combo
    model_config_metadata = defaultdict(lambda: {
        'model_id': None,
        'config': None,
        'traces': []
    })

    # Scan all JSON files
    json_files = list(results_dir.rglob("*.json"))
    print(f"Found {len(json_files)} trace files")

    for json_file in json_files:
        try:
            # Parse directory structure to extract model_id and config
            parts = json_file.relative_to(results_dir).parts

            if len(parts) < 4:
                continue

            model_id = parts[0]
            config = parts[1]  # with_fray or without_fray

            # Check if this is in a repetition directory
            if not parts[2].startswith("rep_"):
                continue

            with open(json_file, 'r') as f:
                trace = json.load(f)

            # Extract key fields
            success = trace.get('success', False)
            category = trace.get('benchmark_category', 'unknown')
            task_type = trace.get('task_type', 'unknown')
            instance_id = trace.get('instance_id', json_file.stem)

            # Relative path from results dir
            rel_path = json_file.relative_to(results_dir)

            # Store result by model+config+instance
            key = (model_id, config)
            instance_results[key][instance_id].append(success)

            # Store metadata
            if model_config_metadata[key]['model_id'] is None:
                model_config_metadata[key]['model_id'] = model_id
                model_config_metadata[key]['config'] = config

            model_config_metadata[key]['traces'].append({
                'instance_id': instance_id,
                'path': str(rel_path),
                'success': success,
                'category': category,
                'task_type': task_type
            })

        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            continue

    # Now compute averaged statistics for each model+config combination
    model_stats = {}

    for (model_id, config), instances in instance_results.items():
        # Create display name
        friendly_name = get_friendly_name(model_id)
        config_display = config.replace("_", " ")
        display_name = f"{friendly_name} ({config_display})"

        # Compute average success rate per instance
        total_instances = len(instances)
        successful_instances = 0
        total_attempts = 0
        successful_attempts = 0

        for instance_id, successes in instances.items():
            total_attempts += len(successes)
            successful_attempts += sum(successes)
            # Average over repetitions for this instance
            avg_success = sum(successes) / len(successes) if successes else 0
            # Count as successful if average is > 0.5 (majority of reps succeeded)
            if avg_success > 0.5:
                successful_instances += 1

        success_rate = (successful_instances / total_instances * 100) if total_instances > 0 else 0
        num_reps = len(list(instances.values())[0]) if instances else 0

        model_stats[display_name] = {
            'model_id': model_id,
            'config': config,
            'display_name': display_name,
            'total': total_instances,
            'success': successful_instances,
            'failure': total_instances - successful_instances,
            'success_rate': success_rate,
            'num_repetitions': num_reps,
            'total_attempts': total_attempts,
            'successful_attempts': successful_attempts,
            'raw_success_rate': (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0,
            'traces': model_config_metadata[(model_id, config)]['traces']
        }

    # Create summary
    summary = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'total_traces': len(json_files),
        'models': model_stats,
    }

    # Write to output file
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"Aggregated {len(json_files)} traces")
    print(f"Model configurations found: {len(model_stats)}")
    print(f"Summary written to: {output_file}")

    # Print summary
    print("\n=== Leaderboard ===")
    print(f"{'Model':<50} {'Success Rate':<15} {'Instances':<15} {'Raw Rate':<15}")
    print("=" * 95)
    sorted_models = sorted(model_stats.items(), key=lambda x: x[1]['success_rate'], reverse=True)
    for display_name, stats in sorted_models:
        success_pct = f"{stats['success_rate']:.1f}%"
        instances = f"{stats['success']}/{stats['total']}"
        raw_pct = f"{stats['raw_success_rate']:.1f}% ({stats['successful_attempts']}/{stats['total_attempts']})"
        print(f"{display_name:<50} {success_pct:<15} {instances:<15} {raw_pct:<15}")


if __name__ == "__main__":
    import sys

    script_dir = Path(__file__).resolve().parent
    results_dir = script_dir.parent / "results"
    output_file = script_dir / "leaderboard_data.json"

    if len(sys.argv) > 1:
        results_dir = Path(sys.argv[1])

    if not results_dir.exists():
        print(f"Error: Results directory not found: {results_dir}")
        sys.exit(1)

    aggregate_results(results_dir, output_file)
