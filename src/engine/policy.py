import random

from src.models.learner import Problem, SkillAssessment


def select_next_problem(assessment: SkillAssessment, problems: list[Problem]) -> Problem:
    """Pick a problem with 80/20 exploit/explore policy."""
    if not problems:
        raise ValueError("problems cannot be empty")

    target = assessment.next_recommended_difficulty
    candidates = [p for p in problems if abs(p.difficulty - target) <= 1.0]

    # 80% exploit nearby difficulty, 20% explore full pool.
    if candidates and random.random() < 0.8:
        return random.choice(candidates)
    return random.choice(problems)
