#!/usr/bin/env python3
"""Post-process SCTBench patches to show only diffs, not entire files."""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path

RESULTS_DIR = Path("results")
BENCHMARKS_DIR = Path("benchmarks/SCTBench")


def find_original_file(instance_id: str) -> Path | None:
    """Find the original Java file for an instance_id."""
    # For SCTBench, instance_id is the class name (e.g., "Reorder3Bad")
    java_file = f"{instance_id}.java"

    # Search for the file in benchmarks/SCTBench
    for root, dirs, files in os.walk(BENCHMARKS_DIR):
        if java_file in files:
            return Path(root) / java_file

    return None


def process_patch_file(patch_file: Path):
    """Process a single patch file to create a proper diff."""
    instance_id = patch_file.stem  # e.g., "Reorder3Bad" from "Reorder3Bad.patch"

    # Read the patch
    with open(patch_file, "r") as f:
        patch_content = f.read()

    # If the patch is empty, skip
    if not patch_content.strip():
        print(f"Skipping {instance_id}: empty patch")
        return

    # Check if this patch has already been fixed (has an actual diff, not just new file mode)
    if "diff --git a/temp.patch" in patch_content:
        # This patch has the embedded temp.patch from a previous run - remove it
        lines = patch_content.split("\n")
        clean_lines = []
        for line in lines:
            if line.startswith("diff --git a/temp.patch"):
                break
            clean_lines.append(line)

        # Write the cleaned patch
        with open(patch_file, "w") as f:
            f.write("\n".join(clean_lines).rstrip() + "\n")

        print(f"Cleaned patch for {instance_id}")
        return

    # This is an original patch that needs processing
    # Find the original file
    original_file = find_original_file(instance_id)
    if not original_file:
        print(f"Warning: Could not find original file for {instance_id}")
        return

    # Extract only the .java file diff from the patch (ignore .class files)
    # Find the section for the .java file
    java_filename = f"{instance_id}.java"
    lines = patch_content.split("\n")
    java_patch_lines = []
    in_java_section = False

    for i, line in enumerate(lines):
        if line.startswith(f"diff --git") and java_filename in line:
            in_java_section = True
        elif line.startswith("diff --git") and java_filename not in line:
            in_java_section = False

        if in_java_section:
            java_patch_lines.append(line)

    if not java_patch_lines:
        print(f"Warning: No .java diff found in patch for {instance_id}")
        return

    java_patch_content = "\n".join(java_patch_lines)

    # Create a temporary directory to work in
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Copy original file
        temp_file = tmpdir / f"{instance_id}.java"
        shutil.copy2(original_file, temp_file)

        # Initialize git and commit original
        subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=tmpdir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Original"],
            cwd=tmpdir,
            capture_output=True,
        )

        # Write the extracted java-only patch to a temporary file
        temp_patch = tmpdir / "temp.patch"
        with open(temp_patch, "w") as f:
            f.write(java_patch_content)

        # If the patch is creating a new file, remove the existing file first
        if "new file mode" in java_patch_content or "--- /dev/null" in java_patch_content:
            temp_file.unlink()

        # Apply the java-only patch
        patch_result = subprocess.run(
            ["git", "apply", str(temp_patch)],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )

        if patch_result.returncode != 0:
            print(f"Warning: Failed to apply patch for {instance_id}: {patch_result.stderr}")
            return

        # Remove the temporary patch file so it doesn't get included in the diff
        temp_patch.unlink()

        # Create new diff
        subprocess.run(["git", "add", "-A"], cwd=tmpdir, capture_output=True)
        diff_result = subprocess.run(
            ["git", "diff", "--cached"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )

        if not diff_result.stdout.strip():
            print(f"Skipping {instance_id}: no changes detected")
            return

        # Write the new patch
        with open(patch_file, "w") as f:
            f.write(diff_result.stdout)

        print(f"Fixed patch for {instance_id}")


def main():
    """Process all SCTBench patches in results directory."""
    if not RESULTS_DIR.exists():
        print(f"Error: {RESULTS_DIR} does not exist")
        return

    # Find all patch files in SCTBench results
    patch_files = []
    for root, dirs, files in os.walk(RESULTS_DIR):
        # Look for sctbench subdirectories
        if "sctbench" in Path(root).parts:
            for file in files:
                if file.endswith(".patch"):
                    patch_files.append(Path(root) / file)

    print(f"Found {len(patch_files)} SCTBench patch files")

    for patch_file in patch_files:
        process_patch_file(patch_file)

    print("\nDone!")


if __name__ == "__main__":
    main()
