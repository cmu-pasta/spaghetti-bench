import os
from pathlib import Path
from subprocess import run
from typing import List

from concurrency_bench.tasks.loaders.real_world_junit_loader import RealWorldJUnitLoader


class LuceneLoader(RealWorldJUnitLoader):
    """Loader for Apache Lucene concurrency tests.

    Lucene uses Gradle as its build system and is tested with JUnit 5.
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
            junit_version="junit5",
            fray_args=fray_args,
        )

    def apply_patches(self, repo_path: Path):
        patch_file = (
            Path(__file__).parent.parent.parent.parent.parent
            / "benchmarks"
            / "patches"
            / "lucene.patch"
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

        print("Building Lucene with Gradle (this may take several minutes)...")
        print(f"Repository path: {repo_path}")

        # Make gradlew executable
        gradlew_path = repo_path / "gradlew"
        if gradlew_path.exists():
            os.chmod(gradlew_path, 0o755)
            print(f"Made gradlew executable: {gradlew_path}")
        else:
            print(f"Warning: gradlew not found at {gradlew_path}")
            print(f"Directory contents: {list(repo_path.iterdir())[:10]}")

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

        print("Lucene build completed successfully")

    def get_classpaths(self, workdir: Path) -> List[str]:
        """Get classpaths for Lucene tests."""
        repo_path = workdir / self.repo_dir_name
        lucene_core_build = repo_path / "lucene" / "core" / "build"

        classpaths = []

        # Add libs directory
        libs_dir = lucene_core_build / "libs"
        if libs_dir.exists():
            classpaths.append(str(libs_dir / "*.jar"))

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
        dependency_dir = lucene_core_build / "dependency"
        if dependency_dir.exists():
            classpaths.append(str(dependency_dir / "*.jar"))

        return self._expand_glob_paths(classpaths)

    def get_test_properties(self) -> dict:
        """Lucene tests require specific properties."""
        workdir = Path.cwd()  # Will be set correctly when run() is called
        repo_path = workdir / self.repo_dir_name if hasattr(self, 'repo_dir_name') else workdir / "repo"

        return {
            "tests.seed": "deadbeef",
            "tests.jvmForkArgsFile": str(repo_path / "lucene" / "core" / "build" / "tmp" / "test" / "jvm-forking.properties"),
        }

    def get_fray_configs(self) -> List[str]:
        return [
            "--iter",
            "5000",
            "--no-reset-class-loader",
            "--scheduler",
            "pos",
        ]
