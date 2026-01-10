import os
from pathlib import Path
from subprocess import run
from typing import List

from concurrency_bench.tasks.loaders.real_world_junit_loader import RealWorldJUnitLoader


class KafkaLoader(RealWorldJUnitLoader):
    """Loader for Apache Kafka concurrency tests.

    Kafka uses Gradle as its build system and is tested with JUnit 5.
    """

    def __init__(
        self,
        task_name: str,
        repo_url: str,
        commit: str,
        test_class: str,
        test_method: str,
    ):
        super().__init__(
            task_name=task_name,
            repo_url=repo_url,
            commit=commit,
            test_class=test_class,
            test_method=test_method,
            junit_version="junit5",
        )

    def apply_patches(self, repo_path: Path):
        patch_file = (
            Path(__file__).parent.parent.parent.parent.parent
            / "benchmarks"
            / "patches"
            / "kafka.patch"
        )

        if not patch_file.exists():
            print(f"Warning: Patch file not found at {patch_file}")
            return

        print(f"Applying patch from {patch_file}...")
        result = run(
            ["git", "apply", str(patch_file)],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            print(f"Warning: Failed to apply patch: {result.stderr}")
        else:
            print("Successfully applied patch")

    def build(self, workdir: Path):
        repo_path = workdir / self.repo_dir_name

        print("Building Kafka with Gradle (this may take several minutes)...")

        print("Running ./gradlew testJar...")
        result = run(
            ["./gradlew", "testJar", "--no-daemon"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to build testJar: {result.stderr}")

        print("Running ./gradlew jar...")
        result = run(
            ["./gradlew", "jar", "--no-daemon"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to build jar: {result.stderr}")

        print("Running ./gradlew copyDependencies...")
        result = run(
            ["./gradlew", "copyDependencies", "--no-daemon"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to copy dependencies: {result.stderr}")

        print("Kafka build completed successfully")

    def get_classpaths(self, workdir: Path) -> List[str]:
        """Get classpaths for Kafka Streams tests."""
        repo_path = workdir / self.repo_dir_name
        streams_build = repo_path / "streams" / "build"

        classpaths = [
            str(streams_build / "classes" / "java" / "main"),
            str(streams_build / "classes" / "java" / "test"),
            str(streams_build / "resources" / "test"),
            str(streams_build / "resources" / "main"),
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
        dependency_dir = streams_build / "dependency"
        if dependency_dir.exists():
            classpaths.append(str(dependency_dir / "*.jar"))

        return self._expand_glob_paths(classpaths)

    def get_test_properties(self) -> dict:
        """Kafka tests don't require special properties."""
        return {}

    def get_fray_configs(self) -> List[str]:
        return ["--iter", "10000", "--sleep-as-yield", "--no-reset-class-loader"]
