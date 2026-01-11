import os
from pathlib import Path
from subprocess import run
from typing import List

from concurrency_bench.tasks.loaders.real_world_junit_loader import RealWorldJUnitLoader


class UniffleLoader(RealWorldJUnitLoader):
    """Loader for Uniffle concurrency tests."""

    def __init__(
        self,
        task_name: str,
        repo_url: str,
        commit: str,
        test_class: str,
        test_method: str,
        fray_args: List[str] = [],
    ):
        super().__init__(
            task_name=task_name,
            repo_url=repo_url,
            commit=commit,
            test_class=test_class,
            test_method=test_method,
            junit_version="junit5",
            fray_args=fray_args,
        )

    def build(self, workdir: Path):
        repo_path = workdir / self.repo_dir_name

        print("Building Uniffle project...")

        print("Running mvn -DskipTests install...")
        result = run(
            ["mvn", "-DskipTests", "install"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to build uniffle: {result.stderr}")

        print("Running mvn copy-dependencies...")
        result = run(
            ["mvn", "dependency:copy-dependencies"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to copy dependencies: {result.stderr}")

        print("Uniffle build completed successfully")

    def get_classpaths(self, workdir: Path) -> List[str]:
        """Get classpaths for Uniffle tests."""
        repo_path = workdir / self.repo_dir_name
        target_dir = repo_path / "common" / "target"

        classpaths = [
            str(target_dir / "classes"),
            str(target_dir / "test-classes"),
        ]

        junit_runner_jar = (
            Path(__file__).parent.parent.parent.parent.parent
            / "helpers"
            / "junit-runner"
            / "build"
            / "libs"
            / "junit-runner-1.0-SNAPSHOT.jar"
        )
        if junit_runner_jar.exists():
            classpaths.append(str(junit_runner_jar))

        # Add junit-runner dependencies
        junit_runner_deps = (
            Path(__file__).parent.parent.parent.parent.parent
            / "helpers"
            / "junit-runner"
            / "build"
            / "dependency"
        )
        if junit_runner_deps.exists():
            classpaths.append(str(junit_runner_deps / "*"))

        # Add all dependency JARs
        dependency_dir = target_dir / "dependency"
        if dependency_dir.exists():
            classpaths.append(str(dependency_dir / "*.jar"))
        dependency_dir = target_dir / "jars"
        if dependency_dir.exists():
            classpaths.append(str(dependency_dir / "*.jar"))

        return self._expand_glob_paths(classpaths)

    def get_test_properties(self) -> dict:
        return {}

    def get_fray_configs(self) -> List[str]:
        return [
            "--iter",
            "5000",
            "--no-reset-class-loader",
            "--scheduler",
            "pos",
        ]
