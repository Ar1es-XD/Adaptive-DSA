import time
from typing import Any

from src.data.loader import get_problem_by_id, get_problems_by_topic, load_problems
from src.db.storage import LearnerDB
from src.engine.evaluator import ProblemEvaluator
from src.engine.learner_model import (
    apply_forgetting,
    assess_mastery,
    compute_overall_proficiency,
    initialize_problem_state,
    initialize_skill_state,
    is_due_for_review,
    is_problem_due_for_review,
    record_attempt,
    time_to_problem_review_seconds,
    time_to_next_review_seconds,
    update_problem_state_schedule,
)
from src.engine.policy import select_next_problem
from src.models.learner import AttemptRecord
from src.models.learner import AttemptLog

_db = LearnerDB("learner.db")
_evaluator = ProblemEvaluator()
_problem_start_times: dict[str, float] = {}
_incorrect_counts: dict[str, int] = {}
_attempt_counts: dict[str, int] = {}
MAX_ATTEMPTS_PER_PROBLEM = 3


def _problem_to_dict(problem) -> dict[str, Any]:
    return {
        "problem_id": problem.problem_id,
        "title": problem.title,
        "description": problem.description,
        "topic": problem.topic,
        "difficulty": problem.difficulty,
        "pattern": problem.pattern,
    }


def _assessment_to_dict(assessment) -> dict[str, Any]:
    return {
        "skill_id": assessment.skill_id,
        "estimated_mastery": assessment.estimated_mastery,
        "confidence": assessment.confidence,
        "ready_to_advance": assessment.ready_to_advance,
        "should_review": assessment.should_review,
        "next_recommended_difficulty": assessment.next_recommended_difficulty,
    }


def _meta_from_assessment(assessment) -> dict[str, Any]:
    return {
        "mastery": assessment.estimated_mastery,
        "confidence": assessment.confidence,
    }


def _load_problem_states_for_topic(topic: str) -> dict[str, Any]:
    states: dict[str, Any] = {}
    for problem in get_problems_by_topic(topic):
        ps = _db.load_problem_state(problem.problem_id)
        if ps is not None:
            states[problem.problem_id] = ps
    return states


def start_session(topic: str) -> dict:
    problems = get_problems_by_topic(topic)
    if not problems:
        return {"error": f"No problems found for topic: {topic}"}

    now = time.time()
    state = _db.load_skill_state(topic) or initialize_skill_state(topic)
    effective_state, decay_applied = apply_forgetting(state, now)
    assessment = assess_mastery(effective_state)

    problem_states = _load_problem_states_for_topic(topic)
    problem = select_next_problem(
        assessment,
        problems,
        topic=topic,
        state=state,
        current_time=now,
        problem_states=problem_states,
    )

    _problem_start_times[problem.problem_id] = now
    _incorrect_counts[problem.problem_id] = 0
    _attempt_counts[problem.problem_id] = 0

    return {
        "problem": _problem_to_dict(problem),
        "feedback": None,
        "next_problem": None,
        "meta": _meta_from_assessment(assessment),
        "topic": topic,
        "assessment": _assessment_to_dict(assessment),
        "decay_applied": round(decay_applied, 2),
        "next_review_hours": round(time_to_next_review_seconds(state, now) / 3600, 2),
    }


def start_problem(problem_id: str) -> dict:
    problem = get_problem_by_id(problem_id)
    if not problem:
        return {"error": f"Unknown problem_id: {problem_id}"}

    now = time.time()
    topic = problem.topic
    state = _db.load_skill_state(topic) or initialize_skill_state(topic)
    effective_state, _ = apply_forgetting(state, now)
    assessment = assess_mastery(effective_state)

    _problem_start_times[problem.problem_id] = now
    _incorrect_counts[problem.problem_id] = 0
    _attempt_counts[problem.problem_id] = 0

    return {
        "problem": _problem_to_dict(problem),
        "feedback": None,
        "next_problem": None,
        "meta": _meta_from_assessment(assessment),
    }


def submit_answer(problem_id: str, answer: str) -> dict:
    problem = get_problem_by_id(problem_id)
    if not problem:
        return {"error": f"Unknown problem_id: {problem_id}"}

    cleaned = answer.strip()
    if not cleaned:
        return {"error": "Empty answer"}

    now = time.time()
    topic = problem.topic
    state = _db.load_skill_state(topic) or initialize_skill_state(topic)

    start_time = _problem_start_times.get(problem_id, now)
    time_spent = max(0.0, now - start_time)
    is_correct = _evaluator.check_solution(problem, cleaned)
    attempts_on_problem = _attempt_counts.get(problem_id, 0) + 1
    _attempt_counts[problem_id] = attempts_on_problem

    attempt = AttemptRecord(
        timestamp=now,
        problem_id=problem.problem_id,
        success=is_correct,
        time_spent_seconds=time_spent,
        problem_difficulty=problem.difficulty,
        user_id="default_learner",
    )

    state = record_attempt(state, attempt)
    _db.save_skill_state(state)
    assessment = assess_mastery(state)

    problem_state = _db.load_problem_state(problem.problem_id) or initialize_problem_state(
        problem.problem_id,
        now,
    )
    updated_problem_state, quality = update_problem_state_schedule(problem_state, attempt, assessment.confidence)
    _db.save_problem_state(updated_problem_state)
    _db.save_attempt_log(
        AttemptLog(
            timestamp=attempt.timestamp,
            problem_id=attempt.problem_id,
            success=attempt.success,
            time_spent_seconds=attempt.time_spent_seconds,
            quality=quality,
            interval_days=updated_problem_state.interval_days,
            confidence=assessment.confidence,
        )
    )

    hint = None
    if not is_correct:
        _incorrect_counts[problem_id] = _incorrect_counts.get(problem_id, 0) + 1
        hint = _evaluator.get_hint(problem, _incorrect_counts[problem_id])
    else:
        _incorrect_counts[problem_id] = 0

    topic_problems = get_problems_by_topic(topic)
    problem_states = _load_problem_states_for_topic(topic)
    next_problem = select_next_problem(
        assessment,
        topic_problems,
        topic=topic,
        state=state,
        current_time=now,
        problem_states=problem_states,
    )
    _problem_start_times[next_problem.problem_id] = now
    _attempt_counts[next_problem.problem_id] = _attempt_counts.get(next_problem.problem_id, 0)

    max_attempts_reached = (not is_correct) and (attempts_on_problem >= MAX_ATTEMPTS_PER_PROBLEM)
    show_solution = max_attempts_reached
    solution = problem.expected_output if show_solution else None

    if is_correct or max_attempts_reached:
        _attempt_counts[problem_id] = 0
        _incorrect_counts[problem_id] = 0

    return {
        "problem": _problem_to_dict(problem),
        "assessment": _assessment_to_dict(assessment),
        "feedback": {
            "correct": is_correct,
            "hint": hint,
            "mastery": assessment.estimated_mastery,
            "confidence": assessment.confidence,
        },
        "next_problem": _problem_to_dict(next_problem),
        "meta": _meta_from_assessment(assessment),
        "control": {
            "attempts_on_problem": attempts_on_problem,
            "max_attempts_reached": max_attempts_reached,
            "show_solution": show_solution,
        },
        "solution": solution,
    }


def get_status(topic: str) -> dict:
    state = _db.load_skill_state(topic)
    if not state:
        return {"error": f"No data for {topic} yet"}

    now = time.time()
    effective_state, decay_applied = apply_forgetting(state, now)
    assessment = assess_mastery(effective_state)

    return {
        "topic": topic,
        "mastery": assessment.estimated_mastery,
        "confidence": assessment.confidence,
        "attempts": state.attempt_count,
        "ready_to_advance": assessment.ready_to_advance,
        "next_difficulty": assessment.next_recommended_difficulty,
        "due_for_review": is_due_for_review(state, now),
        "next_review_hours": round(time_to_next_review_seconds(state, now) / 3600, 2),
        "effective_decay": round(decay_applied, 2),
    }


def get_review() -> list:
    all_problems = load_problems()
    now = time.time()
    rows = []

    for problem in all_problems:
        ps = _db.load_problem_state(problem.problem_id) or initialize_problem_state(problem.problem_id, now)
        due = is_problem_due_for_review(ps, problem.difficulty, now)
        hours_to_review = time_to_problem_review_seconds(ps, problem.difficulty, now) / 3600
        near_due = hours_to_review <= 6
        status_label = "DUE" if due else ("NEAR-DUE" if near_due else "UPCOMING")
        priority = 0 if due else (1 if near_due else 2)
        rows.append(
            {
                "_priority": priority,
                "topic": problem.topic,
                "problem_id": problem.problem_id,
                "status": status_label,
                "next_review_hours": round(hours_to_review, 2),
                "interval_days": round(ps.interval_days, 2),
                "interval": round(ps.interval_days, 2),
                "ease_factor": round(ps.ease_factor, 2),
            }
        )

    rows.sort(key=lambda row: (row["_priority"], row["next_review_hours"]))
    for row in rows:
        row.pop("_priority", None)
    return rows


def get_recommend() -> list:
    all_problems = load_problems()
    topics = sorted({p.topic for p in all_problems})
    now = time.time()

    topic_rows = []
    skill_states = []
    for topic in topics:
        state = _db.load_skill_state(topic) or initialize_skill_state(topic)
        effective_state, _ = apply_forgetting(state, now)
        assessment = assess_mastery(effective_state)
        topic_rows.append((assessment.estimated_mastery, topic, assessment, state))
        skill_states.append(effective_state)

    topic_rows.sort(key=lambda x: x[0])

    recommendations = []
    seen = set()
    for _, topic, assessment, state in topic_rows:
        if len(recommendations) >= 3:
            break
        topic_problems = [p for p in all_problems if p.topic == topic]
        if not topic_problems:
            continue
        problem_states = _load_problem_states_for_topic(topic)

        candidate = select_next_problem(
            assessment,
            topic_problems,
            topic=topic,
            state=state,
            current_time=now,
            problem_states=problem_states,
        )
        if candidate.problem_id in seen:
            continue
        seen.add(candidate.problem_id)
        recommendations.append(
            {
                "topic": topic,
                "problem": _problem_to_dict(candidate),
                "target_difficulty": assessment.next_recommended_difficulty,
                "skill_mastery": assessment.estimated_mastery,
                "overall_proficiency": None,
            }
        )

    overall = compute_overall_proficiency(skill_states)
    for row in recommendations:
        row["overall_proficiency"] = overall
    return recommendations


def get_analytics_summary() -> dict:
    base = _db.get_attempt_summary()
    now = time.time()
    all_problems = load_problems()
    topics = sorted({p.topic for p in all_problems})

    weak = []
    for topic in topics:
        state = _db.load_skill_state(topic)
        if not state:
            continue
        effective_state, _ = apply_forgetting(state, now)
        assessment = assess_mastery(effective_state)
        if assessment.estimated_mastery < 50:
            weak.append((assessment.estimated_mastery, topic))

    weak.sort(key=lambda x: x[0])
    base["weak_topics"] = [topic for _, topic in weak]
    return base
