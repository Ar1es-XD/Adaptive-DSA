import time

from src.engine.learner_model import (
    initialize_problem_state,
    initialize_skill_state,
    record_attempt,
    update_problem_state_schedule,
)
from src.models.learner import AttemptRecord


def test_each_problem_evolves_independently():
    now = time.time()
    skill_state = initialize_skill_state("arrays")

    ps_a = initialize_problem_state("array_001", now)
    ps_b = initialize_problem_state("array_002", now)

    attempt_a = AttemptRecord(
        timestamp=now,
        problem_id="array_001",
        success=True,
        time_spent_seconds=10.0,
        problem_difficulty=2.0,
        user_id="default_learner",
    )

    skill_state = record_attempt(skill_state, attempt_a)
    ps_a_updated, _ = update_problem_state_schedule(ps_a, attempt_a, confidence=80)

    assert ps_a_updated.repetitions == 1
    assert ps_b.repetitions == 0


def test_failure_on_one_problem_does_not_reset_other_problem():
    now = time.time()
    ps_a = initialize_problem_state("array_001", now)
    ps_b = initialize_problem_state("array_002", now)

    success_a = AttemptRecord(
        timestamp=now,
        problem_id="array_001",
        success=True,
        time_spent_seconds=10.0,
        problem_difficulty=2.0,
        user_id="default_learner",
    )
    failure_b = AttemptRecord(
        timestamp=now + 5,
        problem_id="array_002",
        success=False,
        time_spent_seconds=120.0,
        problem_difficulty=4.0,
        user_id="default_learner",
    )

    ps_a, _ = update_problem_state_schedule(ps_a, success_a, confidence=80)
    ps_b, _ = update_problem_state_schedule(ps_b, failure_b, confidence=20)

    assert ps_a.repetitions >= 1
    assert ps_b.repetitions == 0


def test_due_problem_state_selection_signal():
    now = time.time()
    ps = initialize_problem_state("array_001", now)
    ps.interval_days = 1.0
    ps.last_seen_timestamp = now - (2 * 86400)

    assert (ps.last_seen_timestamp + ps.interval_days * 86400) <= now


def test_problem_sm2_progression_over_multiple_successes():
    now = time.time()
    ps = initialize_problem_state("array_001", now)
    attempts = [
        AttemptRecord(
            timestamp=now,
            problem_id="array_001",
            success=True,
            time_spent_seconds=10.0,
            problem_difficulty=2.0,
            user_id="default_learner",
        ),
        AttemptRecord(
            timestamp=now + 5,
            problem_id="array_001",
            success=True,
            time_spent_seconds=10.0,
            problem_difficulty=2.0,
            user_id="default_learner",
        ),
        AttemptRecord(
            timestamp=now + 10,
            problem_id="array_001",
            success=True,
            time_spent_seconds=10.0,
            problem_difficulty=2.0,
            user_id="default_learner",
        ),
    ]
    for att in attempts:
        ps, _ = update_problem_state_schedule(ps, att, confidence=80)

    assert ps.repetitions == 3
    assert ps.interval_days > 6.0


def test_problem_failure_resets_only_that_problem_schedule():
    now = time.time()
    ps_a = initialize_problem_state("array_001", now)
    ps_b = initialize_problem_state("array_002", now)

    success = AttemptRecord(
        timestamp=now,
        problem_id="array_001",
        success=True,
        time_spent_seconds=10.0,
        problem_difficulty=2.0,
        user_id="default_learner",
    )
    failure = AttemptRecord(
        timestamp=now + 5,
        problem_id="array_002",
        success=False,
        time_spent_seconds=120.0,
        problem_difficulty=2.0,
        user_id="default_learner",
    )

    ps_a, _ = update_problem_state_schedule(ps_a, success, confidence=80)
    ps_b, _ = update_problem_state_schedule(ps_b, failure, confidence=20)

    assert ps_a.repetitions >= 1
    assert ps_b.repetitions == 0
