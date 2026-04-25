import random
import time

from src.engine.learner_model import is_problem_due_for_review, time_to_problem_review_seconds
from src.models.learner import LearnerSkillState, Problem, SkillAssessment
from src.models.problem_state import ProblemState

LOW_CONFIDENCE_REVIEW_THRESHOLD = 40.0
NEAR_DUE_SECONDS = 6 * 3600


def select_next_problem(
    assessment: SkillAssessment,
    problems: list[Problem],
    topic: str | None = None,
    state: LearnerSkillState | None = None,
    current_time: float | None = None,
    problem_states: dict[str, ProblemState] | None = None,
) -> Problem:
    """Select next problem using problem-level review state with skill-level fallback."""
    if not problems:
        raise ValueError("problems cannot be empty")

    now = current_time if current_time is not None else time.time()

    filtered_problems = [p for p in problems if p.topic == topic] if topic else problems
    if not filtered_problems:
        filtered_problems = problems

    target = assessment.next_recommended_difficulty
    candidates = [p for p in filtered_problems if abs(p.difficulty - target) <= 1.0]

    problem_states = problem_states or {}

    due_candidates = [
        p for p in problems
        if p.problem_id in problem_states and is_problem_due_for_review(problem_states[p.problem_id], p.difficulty, now)
    ]
    if due_candidates:
        return random.choice(due_candidates)

    near_due_candidates = [
        p for p in problems
        if p.problem_id in problem_states
        and time_to_problem_review_seconds(problem_states[p.problem_id], p.difficulty, now) <= NEAR_DUE_SECONDS
    ]
    if near_due_candidates:
        return random.choice(near_due_candidates)

    low_confidence = assessment.confidence < LOW_CONFIDENCE_REVIEW_THRESHOLD
    if low_confidence:
        reinforcement_candidates = [p for p in filtered_problems if p.difficulty <= max(target, 2.0)]
        if reinforcement_candidates and random.random() < 0.85:
            return random.choice(reinforcement_candidates)
        if candidates:
            return random.choice(candidates)
        return random.choice(filtered_problems)

    # 80% exploit nearby difficulty, 20% explore full pool.
    if candidates and random.random() < 0.8:
        return random.choice(candidates)
    return random.choice(filtered_problems)
