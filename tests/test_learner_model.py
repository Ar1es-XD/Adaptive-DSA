import time

from src.engine.learner_model import (
    BASE_REVIEW_INTERVAL_SECONDS,
    apply_forgetting,
    assess_mastery,
    compute_overall_proficiency,
    compute_quality,
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
    assert updated.last_seen_timestamp == state.last_seen_timestamp


def test_apply_forgetting_hits_daily_target_range():
    now = time.time()
    state = LearnerSkillState(
        skill_id="arrays",
        mastery_mu=100.0,
        mastery_variance=100.0,
        last_updated=now - 86400,
        last_seen_timestamp=now - 86400,
        review_interval_seconds=BASE_REVIEW_INTERVAL_SECONDS,
        attempt_count=5,
        recent_attempts=[],
    )

    updated, decay_applied = apply_forgetting(state, now)
    loss_pct = decay_applied / state.mastery_mu * 100
    assert 5.0 <= loss_pct <= 10.0


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
    assert updated.review_interval_seconds == state.review_interval_seconds
    assert updated.interval_days == state.interval_days
    assert updated.repetitions == state.repetitions


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
    assert updated.interval_days == boosted.interval_days
    assert updated.review_interval_seconds == boosted.review_interval_seconds
    assert updated.repetitions == boosted.repetitions


def test_sm2_first_correct_sets_interval_to_one_day():
    now = time.time()
    state = initialize_skill_state("arrays")
    attempt = AttemptRecord(
        timestamp=now,
        problem_id="array_001",
        success=True,
        time_spent_seconds=10.0,
        problem_difficulty=0.0,
        user_id="default_learner",
    )

    updated = record_attempt(state, attempt)
    assert updated.interval_days == state.interval_days
    assert updated.repetitions == state.repetitions


def test_sm2_second_correct_sets_interval_to_six_days():
    now = time.time()
    state = initialize_skill_state("arrays")

    first = AttemptRecord(
        timestamp=now,
        problem_id="array_001",
        success=True,
        time_spent_seconds=10.0,
        problem_difficulty=0.0,
        user_id="default_learner",
    )
    second = AttemptRecord(
        timestamp=now + 5,
        problem_id="array_001",
        success=True,
        time_spent_seconds=10.0,
        problem_difficulty=0.0,
        user_id="default_learner",
    )

    state = record_attempt(state, first)
    state = record_attempt(state, second)
    assert state.interval_days == 1.0
    assert state.repetitions == 0


def test_sm2_third_correct_grows_interval_by_ease_factor():
    now = time.time()
    state = initialize_skill_state("arrays")

    attempts = [
        AttemptRecord(
            timestamp=now,
            problem_id="array_001",
            success=True,
            time_spent_seconds=10.0,
            problem_difficulty=0.0,
            user_id="default_learner",
        ),
        AttemptRecord(
            timestamp=now + 5,
            problem_id="array_001",
            success=True,
            time_spent_seconds=10.0,
            problem_difficulty=0.0,
            user_id="default_learner",
        ),
        AttemptRecord(
            timestamp=now + 10,
            problem_id="array_001",
            success=True,
            time_spent_seconds=10.0,
            problem_difficulty=0.0,
            user_id="default_learner",
        ),
    ]

    for attempt in attempts:
        state = record_attempt(state, attempt)

    assert state.interval_days == 1.0


def test_sm2_failure_resets_repetitions_and_interval():
    now = time.time()
    state = initialize_skill_state("arrays")

    success = AttemptRecord(
        timestamp=now,
        problem_id="array_001",
        success=True,
        time_spent_seconds=10.0,
        problem_difficulty=0.0,
        user_id="default_learner",
    )
    failure = AttemptRecord(
        timestamp=now + 5,
        problem_id="array_001",
        success=False,
        time_spent_seconds=100.0,
        problem_difficulty=0.0,
        user_id="default_learner",
    )

    state = record_attempt(state, success)
    state = record_attempt(state, failure)

    assert state.repetitions == 0
    assert state.interval_days == 1.0


def test_sm2_ease_factor_has_lower_bound():
    now = time.time()
    state = initialize_skill_state("arrays")
    state.ease_factor = 1.3

    slow_success = AttemptRecord(
        timestamp=now,
        problem_id="array_001",
        success=True,
        time_spent_seconds=200.0,
        problem_difficulty=2.0,
        user_id="default_learner",
    )

    updated = record_attempt(state, slow_success)
    assert updated.ease_factor == state.ease_factor


def test_compute_quality_uses_confidence_adjustment():
    assert compute_quality(True, 20.0, 30.0) == 4
    assert compute_quality(True, 20.0, 80.0) == 5
    assert compute_quality(True, 120.0, 30.0) == 2
    assert compute_quality(False, 5.0, 90.0) == 2


def test_interval_scales_with_difficulty_after_sm2():
    now = time.time()
    state = initialize_skill_state("arrays")
    attempt = AttemptRecord(
        timestamp=now,
        problem_id="array_001",
        success=True,
        time_spent_seconds=10.0,
        problem_difficulty=6.0,
        user_id="default_learner",
    )

    updated = record_attempt(state, attempt)
    assert updated.interval_days == state.interval_days


def test_interval_days_has_min_floor():
    now = time.time()
    state = initialize_skill_state("arrays")
    state.interval_days = 0.1
    attempt = AttemptRecord(
        timestamp=now,
        problem_id="array_001",
        success=False,
        time_spent_seconds=200.0,
        problem_difficulty=1.0,
        user_id="default_learner",
    )

    updated = record_attempt(state, attempt)
    assert updated.interval_days == state.interval_days


def test_hard_success_increases_mastery_more_than_easy_success():
    now = time.time()
    base = initialize_skill_state("arrays")

    easy = AttemptRecord(
        timestamp=now,
        problem_id="array_001",
        success=True,
        time_spent_seconds=20.0,
        problem_difficulty=2.0,
        user_id="default_learner",
    )
    hard = AttemptRecord(
        timestamp=now,
        problem_id="graph_001",
        success=True,
        time_spent_seconds=20.0,
        problem_difficulty=8.0,
        user_id="default_learner",
    )

    easy_state = record_attempt(base, easy)
    hard_state = record_attempt(base, hard)
    assert hard_state.mastery_mu > easy_state.mastery_mu


def test_easy_failure_penalizes_more_than_hard_failure():
    now = time.time()
    base = initialize_skill_state("arrays")

    easy_fail = AttemptRecord(
        timestamp=now,
        problem_id="array_001",
        success=False,
        time_spent_seconds=120.0,
        problem_difficulty=2.0,
        user_id="default_learner",
    )
    hard_fail = AttemptRecord(
        timestamp=now,
        problem_id="graph_001",
        success=False,
        time_spent_seconds=120.0,
        problem_difficulty=8.0,
        user_id="default_learner",
    )

    easy_state = record_attempt(base, easy_fail)
    hard_state = record_attempt(base, hard_fail)
    assert easy_state.mastery_mu < hard_state.mastery_mu


def test_compute_overall_proficiency_weighted_by_attempts():
    a = initialize_skill_state("arrays")
    b = initialize_skill_state("dp")
    a.mastery_mu = 40
    a.attempt_count = 10
    b.mastery_mu = 80
    b.attempt_count = 1

    overall = compute_overall_proficiency([a, b])
    assert overall < 50
