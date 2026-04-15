"""Save and restore progress so long runs can be interrupted and resumed."""

import json
from pathlib import Path


class Checkpoint:
    def __init__(self, path: Path):
        self.path = path

    def exists(self) -> bool:
        return self.path.exists()

    def save(self, results: list, emails_done: int):
        self.path.write_text(
            json.dumps({"emails_done": emails_done, "results": results}),
            encoding="utf-8",
        )

    def load(self) -> tuple[list, int]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return data["results"], data["emails_done"]

    def delete(self):
        if self.path.exists():
            self.path.unlink()
