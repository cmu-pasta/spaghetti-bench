import os
from pathlib import Path
from subprocess import run
from typing import List

from concurrency_bench.tasks.loaders.real_world_junit_loader import RealWorldJUnitLoader


class GuavaLoader(RealWorldJUnitLoader):
    """Loader for Google Guava concurrency tests.

    Guava uses Maven as its build system and is tested with JUnit 4.
    """

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
            junit_version="junit4",
            fray_args=fray_args,
        )

    def build(self, workdir: Path):
        repo_path = workdir / self.repo_dir_name

        print("Building Guava with Maven (this may take several minutes)...")

        # Build from parent directory first
        print("Running ./mvnw -DskipTests install...")
        result = run(
            ["./mvnw", "-DskipTests", "install"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to build Guava: {result.stderr}")

        # Build guava-tests module
        guava_tests_path = repo_path / "guava-tests"
        print("Running ../mvnw -DskipTests package...")
        result = run(
            ["../mvnw", "-DskipTests", "package"],
            cwd=guava_tests_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to build guava-tests: {result.stderr}")

        # Copy dependencies
        print("Running ../mvnw dependency:copy-dependencies...")
        result = run(
            ["../mvnw", "dependency:copy-dependencies"],
            cwd=guava_tests_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to copy dependencies: {result.stderr}")

        print("Guava build completed successfully")

    def get_classpaths(self, workdir: Path) -> List[str]:
        """Get classpaths for Guava tests."""
        repo_path = workdir / self.repo_dir_name
        guava_tests_target = repo_path / "guava-tests" / "target"

        classpaths = []

        # Add test JAR
        test_jar = guava_tests_target / "guava-tests-HEAD-jre-SNAPSHOT-tests.jar"
        if test_jar.exists():
            classpaths.append(str(test_jar))
        else:
            # Fallback to classes directories if JAR not found
            classpaths.extend([
                str(guava_tests_target / "classes"),
                str(guava_tests_target / "test-classes"),
            ])

        # Add junit-runner JAR
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
        dependency_dir = guava_tests_target / "dependency"
        if dependency_dir.exists():
            classpaths.append(str(dependency_dir / "*.jar"))

        return self._expand_glob_paths(classpaths)

    def get_test_properties(self) -> dict:
        """Guava tests don't require special properties."""
        return {}

    def get_fray_configs(self) -> List[str]:
        return [
            "--iter",
            "5000",
            "--no-reset-class-loader",
            "--scheduler",
            "pos",
        ]
