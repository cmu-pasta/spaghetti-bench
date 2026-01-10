import glob
import json
import os
import sys
from pathlib import Path
from subprocess import PIPE, STDOUT, run
from typing import List, Optional

from concurrency_bench.tasks.loaders.task_loader import TaskLoader


class RealWorldJUnitLoader(TaskLoader):
    """Base loader for real-world JUnit tests with Fray.

    This loader handles:
    - Cloning repositories at specific commits
    - Applying build system patches
    - Building projects (subclass-specific)
    - Running tests with Fray and JUnitRunner
    """

    def __init__(
        self,
        task_name: str,
        repo_url: str,
        commit: str,
        test_class: str,
        test_method: str,
        junit_version: str = "junit5",
    ):
        super().__init__(task_name)
        self.repo_url = repo_url
        self.commit = commit
        self.test_class = test_class
        self.test_method = test_method
        self.junit_version = junit_version
        self.repo_dir_name = "repo"

    def clone_repo(self, workdir: Path):
        print(f"Cloning {self.repo_url} at commit {self.commit}...")
        repo_path = workdir / self.repo_dir_name

        result = run(
            ["git", "clone", self.repo_url, str(repo_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to clone repo: {result.stderr}")

        result = run(
            ["git", "checkout", self.commit],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to checkout commit: {result.stderr}")

        print(f"Successfully cloned repo to {repo_path}")

        self.apply_patches(repo_path)

    def apply_patches(self, repo_path: Path):
        """Apply build system patches. Override in subclasses if needed."""
        pass

    def build(self, workdir: Path):
        """Build the project. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement build()")

    def get_classpaths(self, workdir: Path) -> List[str]:
        """Get classpaths for running tests. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement get_classpaths()")

    def get_test_properties(self) -> dict:
        """Get JVM properties for running tests. Override in subclasses if needed."""
        return {}

    def get_fray_configs(self) -> List[str]:
        """Get Fray specific configurations. Override in subclasses if needed."""
        return []

    def run(
        self, workdir: Path, run_command: Optional[List[str]] = None
    ) -> tuple[str, bool]:
        """Run test with Fray."""
        if run_command:
            result = run(
                run_command, cwd=workdir, capture_output=True, text=True, check=False
            )
            return result.stdout + result.stderr, result.returncode == 0
        else:
            return self._run_with_fray(workdir)

    def _run_with_fray(self, workdir: Path) -> tuple[str, bool]:
        """Construct and run Fray command with JUnitRunner."""
        classpaths = self.get_classpaths(workdir)
        classpath_str = ":".join(classpaths)
        fray_work_dir = workdir / "fray_workdir"

        # Build system properties
        properties = self.get_test_properties()

        # Add ByteBuddy experimental flag to support newer Java versions
        properties["net.bytebuddy.experimental"] = "true"

        # Build command: fray -cp <classpath> [--system-props "<props>"] org.pastalab.fray.helpers.JUnitRunner <junit_version> <test_class>#<test_method>
        command = [
            "fray",
            "-cp",
            classpath_str,
        ]

        for k, v in properties.items():
            command.append(f"-J-D{k}={v}")

        command.extend(
            [
                "org.pastalab.fray.helpers.JUnitRunner",
                self.junit_version,
                f"{self.test_class}#{self.test_method}",
            ]
        )

        fray_configs = self.get_fray_configs()
        if fray_configs:
            command.append("--")
            command.extend(fray_configs)
        command.append(f"--output={fray_work_dir}")
        command.append("--redirect-stdout")

        print(f"Running Fray with command: {' '.join(command)}")
        result = run(command, cwd=workdir, capture_output=True, text=True, check=False)

        output = result.stdout + result.stderr
        passed = result.returncode == 0

        return output, passed

    def _expand_glob_paths(self, paths: List[str]) -> List[str]:
        """Expand glob patterns in paths to actual file paths."""
        expanded = []
        for path in paths:
            if "*" in path:
                expanded.extend(glob.glob(path))
            else:
                expanded.append(path)
        return expanded
