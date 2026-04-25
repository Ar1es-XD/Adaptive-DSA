import json
from pathlib import Path

from src.models.learner import Problem


def load_problems() -> list[Problem]:
    """Load all problems from JSON."""
    path = Path(__file__).parent / "problems.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [Problem(**p) for p in data]


def get_problem_by_id(problem_id: str) -> Problem | None:
    """Fetch single problem."""
    problems = load_problems()
    return next((p for p in problems if p.problem_id == problem_id), None)


def get_problems_by_topic(topic: str) -> list[Problem]:
    """Filter by skill topic."""
    problems = load_problems()
    return [p for p in problems if p.topic == topic]


def get_problems_by_difficulty(min_diff: float, max_diff: float) -> list[Problem]:
    """Filter by difficulty range."""
    problems = load_problems()
    return [p for p in problems if min_diff <= p.difficulty <= max_diff]
