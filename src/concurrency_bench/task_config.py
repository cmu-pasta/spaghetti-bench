"""Task data class for concurrency benchmarks."""

from dataclasses import dataclass


@dataclass
class TaskConfig:
    instance_id: str
    description: str
    benchmark_category: str
    subcategory: str
    loader: str
    test_class: str
    test_method: str
    path: str | None = None
    repo_url: str | None = None
    commit: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "TaskConfig":
        return cls(
            instance_id=data["instance_id"],
            description=data.get("description", ""),
            benchmark_category=data.get("benchmark_category", ""),
            subcategory=data.get("subcategory", ""),
            loader=data.get("loader", ""),
            path=data.get("path"),
            repo_url=data.get("repo_url"),
            commit=data.get("commit"),
            test_class=data["test_class"],
            test_method=data["test_method"],
        )

    def to_dict(self) -> dict:
        data = {
            "instance_id": self.instance_id,
            "description": self.description,
            "benchmark_category": self.benchmark_category,
            "subcategory": self.subcategory,
            "loader": self.loader,
            "task_class": self.test_class,
            "task_method": self.test_method,
        }
        if self.path is not None:
            data["path"] = self.path
        if self.repo_url is not None:
            data["repo_url"] = self.repo_url
        if self.commit is not None:
            data["commit"] = self.commit
        return data


class TaskInfo:
    pass
