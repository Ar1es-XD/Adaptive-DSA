import random

from src.models.learner import Problem, SkillAssessment


def select_next_problem(assessment: SkillAssessment, problems: list[Problem]) -> Problem:
    """Pick a random problem near recommended difficulty (+/-1)."""
    if not problems:
        raise ValueError("problems cannot be empty")

    target = assessment.next_recommended_difficulty
    candidates = [p for p in problems if abs(p.difficulty - target) <= 1.0]
    if not candidates:
        candidates = problems
    return random.choice(candidates)
