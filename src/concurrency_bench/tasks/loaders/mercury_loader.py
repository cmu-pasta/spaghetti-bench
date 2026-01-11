from pathlib import Path
from subprocess import run
from typing import List

from concurrency_bench.tasks.loaders.real_world_junit_loader import RealWorldJUnitLoader


class MercuryLoader(RealWorldJUnitLoader):
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

        print("Building Mercury project...")

        print(
            "Running mvn -DskipTests=true -Dmaven.test.skip=true install -pl system/platform-core..."
        )
        result = run(
            [
                "mvn",
                "-DskipTests=true",
                "-Dmaven.test.skip=true",
                "install",
                "-pl",
                "system/platform-core",
            ],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to build mercury: {result.stderr}")

        print("Running mvn test-compile -pl system/platform-core...")
        result = run(
            [
                "mvn",
                "test-compile",
                "-pl",
                "system/platform-core",
            ],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to build mercury: {result.stderr}")

        print("Running mvn copy-dependencies...")
        result = run(
            [
                "mvn",
                "dependency:copy-dependencies",
                "-pl",
                "system/platform-core",
            ],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to copy dependencies: {result.stderr}")

        print("Mercury build completed successfully")

    def get_classpaths(self, workdir: Path) -> List[str]:
        repo_path = workdir / self.repo_dir_name
        target_dir = repo_path / "system" / "platform-core" / "target"
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
