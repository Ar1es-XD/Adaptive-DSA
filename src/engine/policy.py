import random
import time

from src.engine.learner_model import is_due_for_review
from src.models.learner import LearnerSkillState, Problem, SkillAssessment


def select_next_problem(
    assessment: SkillAssessment,
    problems: list[Problem],
    state: LearnerSkillState | None = None,
    current_time: float | None = None,
) -> Problem:
    """Select next problem: due-review first, then 80/20 difficulty policy."""
    if not problems:
        raise ValueError("problems cannot be empty")

    now = current_time if current_time is not None else time.time()

    if state and is_due_for_review(state, now):
        due_candidates = [p for p in problems if p.difficulty <= max(assessment.next_recommended_difficulty, 2.0)]
        if due_candidates:
            return random.choice(due_candidates)
        return random.choice(problems)

    target = assessment.next_recommended_difficulty
    candidates = [p for p in problems if abs(p.difficulty - target) <= 1.0]

    # 80% exploit nearby difficulty, 20% explore full pool.
    if candidates and random.random() < 0.8:
        return random.choice(candidates)
    return random.choice(problems)
