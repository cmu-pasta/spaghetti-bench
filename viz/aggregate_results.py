#!/usr/bin/env python3
"""
Aggregate benchmark results from all trace files.
Creates a summary JSON file with per-model and per-category statistics.
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone


def aggregate_results(results_dir: Path, output_file: Path):
    """Aggregate all trace results into a summary JSON file."""

    # Data structures for aggregation
    model_stats = defaultdict(lambda: {
        'total': 0,
        'success': 0,
        'failure': 0,
        'by_category': defaultdict(lambda: {'total': 0, 'success': 0}),
        'by_task_type': defaultdict(lambda: {'total': 0, 'success': 0}),
        'traces': []
    })

    category_stats = defaultdict(lambda: {
        'total': 0,
        'success': 0,
        'by_model': defaultdict(lambda: {'total': 0, 'success': 0})
    })

    task_type_stats = defaultdict(lambda: {
        'total': 0,
        'success': 0,
        'by_model': defaultdict(lambda: {'total': 0, 'success': 0})
    })

    # Scan all JSON files
    json_files = list(results_dir.rglob("*.json"))
    print(f"Found {len(json_files)} trace files")

    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                trace = json.load(f)

            # Extract key fields
            model_id = trace.get('model_id', 'unknown')
            success = trace.get('success', False)
            category = trace.get('benchmark_category', 'unknown')
            task_type = trace.get('task_type', 'unknown')
            instance_id = trace.get('instance_id', json_file.stem)

            # Relative path from results dir
            rel_path = json_file.relative_to(results_dir)

            # Update model stats
            model_stats[model_id]['total'] += 1
            if success:
                model_stats[model_id]['success'] += 1
            else:
                model_stats[model_id]['failure'] += 1

            model_stats[model_id]['by_category'][category]['total'] += 1
            if success:
                model_stats[model_id]['by_category'][category]['success'] += 1

            model_stats[model_id]['by_task_type'][task_type]['total'] += 1
            if success:
                model_stats[model_id]['by_task_type'][task_type]['success'] += 1

            model_stats[model_id]['traces'].append({
                'instance_id': instance_id,
                'path': str(rel_path),
                'success': success,
                'category': category,
                'task_type': task_type
            })

            # Update category stats
            category_stats[category]['total'] += 1
            if success:
                category_stats[category]['success'] += 1

            category_stats[category]['by_model'][model_id]['total'] += 1
            if success:
                category_stats[category]['by_model'][model_id]['success'] += 1

            # Update task type stats
            task_type_stats[task_type]['total'] += 1
            if success:
                task_type_stats[task_type]['success'] += 1

            task_type_stats[task_type]['by_model'][model_id]['total'] += 1
            if success:
                task_type_stats[task_type]['by_model'][model_id]['success'] += 1

        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            continue

    # Convert defaultdicts to regular dicts for JSON serialization
    def dict_to_regular(d):
        if isinstance(d, defaultdict):
            d = {k: dict_to_regular(v) for k, v in d.items()}
        return d

    model_stats = dict_to_regular(model_stats)
    category_stats = dict_to_regular(category_stats)
    task_type_stats = dict_to_regular(task_type_stats)

    # Calculate percentages
    for model_id, stats in model_stats.items():
        stats['success_rate'] = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0

        for category, cat_stats in stats['by_category'].items():
            cat_stats['success_rate'] = (cat_stats['success'] / cat_stats['total'] * 100) if cat_stats['total'] > 0 else 0

        for task_type, tt_stats in stats['by_task_type'].items():
            tt_stats['success_rate'] = (tt_stats['success'] / tt_stats['total'] * 100) if tt_stats['total'] > 0 else 0

    for category, stats in category_stats.items():
        stats['success_rate'] = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0

        for model_id, model_stats_in_cat in stats['by_model'].items():
            model_stats_in_cat['success_rate'] = (model_stats_in_cat['success'] / model_stats_in_cat['total'] * 100) if model_stats_in_cat['total'] > 0 else 0

    for task_type, stats in task_type_stats.items():
        stats['success_rate'] = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0

        for model_id, model_stats_in_tt in stats['by_model'].items():
            model_stats_in_tt['success_rate'] = (model_stats_in_tt['success'] / model_stats_in_tt['total'] * 100) if model_stats_in_tt['total'] > 0 else 0

    # Create summary
    summary = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'total_traces': len(json_files),
        'models': model_stats,
        'categories': category_stats,
        'task_types': task_type_stats
    }

    # Write to output file
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"Aggregated {len(json_files)} traces")
    print(f"Models found: {len(model_stats)}")
    print(f"Summary written to: {output_file}")

    # Print summary
    print("\n=== Leaderboard ===")
    sorted_models = sorted(model_stats.items(), key=lambda x: x[1]['success_rate'], reverse=True)
    for model_id, stats in sorted_models:
        print(f"{model_id}: {stats['success_rate']:.1f}% ({stats['success']}/{stats['total']})")


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
