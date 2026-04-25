import time

from src.engine.learner_model import (
    BASE_REVIEW_INTERVAL_SECONDS,
    apply_forgetting,
    assess_mastery,
    initialize_skill_state,
    record_attempt,
)
from src.models.learner import AttemptRecord, LearnerSkillState


def test_initialize_skill_state_defaults():
    state = initialize_skill_state("arrays")
    assert state.skill_id == "arrays"
    assert state.mastery_mu == 50.0
    assert state.mastery_variance == 225.0
    assert state.attempt_count == 0
    assert state.review_interval_seconds == BASE_REVIEW_INTERVAL_SECONDS


def test_assess_mastery_shape():
    state = initialize_skill_state("dp")
    assessment = assess_mastery(state)
    assert assessment.skill_id == "dp"
    assert 0 <= assessment.confidence <= 100
    assert 1 <= assessment.next_recommended_difficulty <= 10


def test_mastery_recovers_when_low_and_success_occurs():
    now = time.time()
    state = LearnerSkillState(
        skill_id="graphs",
        mastery_mu=5.0,
        mastery_variance=225.0,
        last_updated=now - 60,
        last_seen_timestamp=now - 60,
        review_interval_seconds=BASE_REVIEW_INTERVAL_SECONDS,
        attempt_count=10,
        recent_attempts=[],
    )
    attempt = AttemptRecord(
        timestamp=now,
        problem_id="graph_001",
        success=True,
        time_spent_seconds=12.0,
        problem_difficulty=6.0,
        user_id="default_learner",
    )

    updated = record_attempt(state, attempt)
    assert updated.mastery_mu >= state.mastery_mu + 4.0


def test_mastery_floor_prevents_zero_lock_on_failure():
    now = time.time()
    state = LearnerSkillState(
        skill_id="arrays",
        mastery_mu=5.0,
        mastery_variance=225.0,
        last_updated=now - 60,
        last_seen_timestamp=now - 60,
        review_interval_seconds=BASE_REVIEW_INTERVAL_SECONDS,
        attempt_count=10,
        recent_attempts=[],
    )
    attempt = AttemptRecord(
        timestamp=now,
        problem_id="array_001",
        success=False,
        time_spent_seconds=10.0,
        problem_difficulty=2.0,
        user_id="default_learner",
    )

    updated = record_attempt(state, attempt)
    assert updated.mastery_mu >= 5.0


def test_mixed_attempts_keep_mastery_in_valid_range():
    now = time.time()
    state = initialize_skill_state("dp")

    attempts = [
        AttemptRecord(
            timestamp=now,
            problem_id="dp_001",
            success=False,
            time_spent_seconds=20.0,
            problem_difficulty=5.0,
            user_id="default_learner",
        ),
        AttemptRecord(
            timestamp=now + 5,
            problem_id="dp_001",
            success=True,
            time_spent_seconds=15.0,
            problem_difficulty=5.0,
            user_id="default_learner",
        ),
    ]

    for attempt in attempts:
        state = record_attempt(state, attempt)

    assert 5.0 <= state.mastery_mu <= 100.0


def test_apply_forgetting_reduces_mastery_over_time():
    now = time.time()
    state = LearnerSkillState(
        skill_id="arrays",
        mastery_mu=80.0,
        mastery_variance=100.0,
        last_updated=now - 86400,
        last_seen_timestamp=now - (86400 * 30),
        review_interval_seconds=BASE_REVIEW_INTERVAL_SECONDS,
        attempt_count=5,
        recent_attempts=[],
    )

    updated, decay_applied = apply_forgetting(state, now)
    assert updated.mastery_mu < state.mastery_mu
    assert decay_applied > 0


def test_correct_attempt_increases_review_interval():
    now = time.time()
    state = initialize_skill_state("arrays")
    attempt = AttemptRecord(
        timestamp=now,
        problem_id="array_001",
        success=True,
        time_spent_seconds=8.0,
        problem_difficulty=2.0,
        user_id="default_learner",
    )

    updated = record_attempt(state, attempt)
    assert updated.review_interval_seconds > state.review_interval_seconds


def test_incorrect_attempt_resets_review_interval():
    now = time.time()
    state = initialize_skill_state("arrays")
    boosted = LearnerSkillState(
        skill_id=state.skill_id,
        mastery_mu=state.mastery_mu,
        mastery_variance=state.mastery_variance,
        last_updated=state.last_updated,
        last_seen_timestamp=state.last_seen_timestamp,
        review_interval_seconds=state.review_interval_seconds * 4,
        attempt_count=state.attempt_count,
        recent_attempts=state.recent_attempts,
    )
    attempt = AttemptRecord(
        timestamp=now,
        problem_id="array_001",
        success=False,
        time_spent_seconds=12.0,
        problem_difficulty=2.0,
        user_id="default_learner",
    )

    updated = record_attempt(boosted, attempt)
    assert updated.review_interval_seconds == BASE_REVIEW_INTERVAL_SECONDS
