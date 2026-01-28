#!/usr/bin/env python3
"""Check coverage of results across models, configurations, and repetitions."""

import json
from pathlib import Path
from collections import defaultdict

# Expected configuration
EXPECTED_MODELS = [
    "bedrock_global.anthropic.claude-sonnet-4-5-20250929-v1_0",  # Claude 4.5 Sonnet
    "bedrock_global.anthropic.claude-opus-4-5-20251101-v1_0",    # Claude 4.5 Opus
    "openai_gpt-5.2",                                             # GPT-5.2
    "openai_gpt-5.1-codex",                                       # GPT-5.2 Codex (note: says 5.1)
    "gemini_gemini-3-pro-preview",                                # Gemini 3.0 Pro
    "gemini_gemini-3-flash-preview",                              # Gemini 3.0 Flash
    "bedrock_qwen.qwen3-coder-480b-a35b-v1_0",                   # Qwen 3 Coder
]

EXPECTED_CONFIGS = ["with_fray", "without_fray"]
EXPECTED_REPS = 5
EXPECTED_PATCHES_PER_CONFIG = 39

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
    }
    return mapping.get(model_id, model_id)

def main():
    results_dir = Path(__file__).parent.parent / "results"

    # Scan results directory
    coverage = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))

    for json_file in results_dir.rglob("*.json"):
        parts = json_file.relative_to(results_dir).parts

        # Skip files not in the expected structure
        if len(parts) < 4:
            continue

        model_id = parts[0]
        config = parts[1]  # with_fray or without_fray

        # Check if this is a repetition directory
        if parts[2].startswith("rep_"):
            rep_num = int(parts[2].split("_")[1])
            # parts[3] = fix_bug, parts[4] = category, parts[5] = instance.json
            if len(parts) >= 6:
                instance_id = parts[5].replace(".json", "")
                coverage[model_id][config][rep_num].add(instance_id)

    # Print coverage report
    print("=" * 100)
    print("COVERAGE REPORT")
    print("=" * 100)
    print()

    # Check each expected model
    for model_id in EXPECTED_MODELS:
        friendly_name = get_friendly_name(model_id)
        print(f"\n{friendly_name} ({model_id})")
        print("-" * 100)

        if model_id not in coverage:
            print(f"  ❌ MISSING ENTIRELY - No results found")
            continue

        for config in EXPECTED_CONFIGS:
            print(f"\n  {config}:")

            if config not in coverage[model_id]:
                print(f"    ❌ MISSING ENTIRELY - No results for this configuration")
                continue

            # Check repetitions
            found_reps = sorted(coverage[model_id][config].keys())
            missing_reps = set(range(1, EXPECTED_REPS + 1)) - set(found_reps)

            if missing_reps:
                print(f"    ⚠️  Missing repetitions: {sorted(missing_reps)}")
            else:
                print(f"    ✓ All {EXPECTED_REPS} repetitions present")

            # Check patches per repetition
            for rep in found_reps:
                patches = coverage[model_id][config][rep]
                patch_count = len(patches)

                if patch_count == EXPECTED_PATCHES_PER_CONFIG:
                    print(f"    ✓ rep_{rep}: {patch_count}/{EXPECTED_PATCHES_PER_CONFIG} patches")
                else:
                    print(f"    ⚠️  rep_{rep}: {patch_count}/{EXPECTED_PATCHES_PER_CONFIG} patches (missing {EXPECTED_PATCHES_PER_CONFIG - patch_count})")

    # Summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)

    # Count actual models found
    actual_models = set(coverage.keys())
    expected_model_set = set(EXPECTED_MODELS)

    missing_models = expected_model_set - actual_models
    extra_models = actual_models - expected_model_set

    print(f"\nExpected models: {len(EXPECTED_MODELS)}")
    print(f"Found models: {len(actual_models)}")

    if missing_models:
        print(f"\n❌ Missing models:")
        for model in sorted(missing_models):
            print(f"  - {get_friendly_name(model)} ({model})")

    if extra_models:
        print(f"\n⚠️  Extra models (not in expected list):")
        for model in sorted(extra_models):
            print(f"  - {model}")

    # Count total expected vs actual
    total_expected = len(EXPECTED_MODELS) * len(EXPECTED_CONFIGS) * EXPECTED_REPS
    total_actual = sum(
        len(coverage[m][c][r])
        for m in coverage
        for c in coverage[m]
        for r in coverage[m][c]
    )

    print(f"\nTotal expected result files: {total_expected * EXPECTED_PATCHES_PER_CONFIG}")
    print(f"Total actual result files: {total_actual}")

    # Detailed missing breakdown
    print("\n" + "=" * 100)
    print("DETAILED MISSING PATCHES")
    print("=" * 100)

    # Load all.jsonl to get expected instance IDs
    all_jsonl = results_dir.parent / "src" / "concurrency_bench" / "all.jsonl"
    expected_instances = set()
    if all_jsonl.exists():
        with open(all_jsonl) as f:
            for line in f:
                if line.strip():
                    task = json.loads(line)
                    expected_instances.add(task["instance_id"])
        print(f"\nExpected instances from all.jsonl: {len(expected_instances)}")

        if len(expected_instances) != EXPECTED_PATCHES_PER_CONFIG:
            print(f"⚠️  WARNING: Expected {EXPECTED_PATCHES_PER_CONFIG} but found {len(expected_instances)} in all.jsonl")

    # Show missing patches for incomplete repetitions
    for model_id in sorted(coverage.keys()):
        for config in sorted(coverage[model_id].keys()):
            for rep in sorted(coverage[model_id][config].keys()):
                patches = coverage[model_id][config][rep]
                if expected_instances and len(patches) < len(expected_instances):
                    missing = expected_instances - patches
                    if missing:
                        print(f"\n{get_friendly_name(model_id)} / {config} / rep_{rep}")
                        print(f"  Missing {len(missing)} patches:")
                        for instance in sorted(missing):
                            print(f"    - {instance}")

if __name__ == "__main__":
    main()
