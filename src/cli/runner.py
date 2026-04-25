import time

import typer

from src.data.loader import get_problems_by_topic, load_problems
from src.db.storage import LearnerDB
from src.engine.evaluator import ProblemEvaluator
from src.engine.learner_model import (
    apply_forgetting,
    assess_mastery,
    compute_overall_proficiency,
    initialize_skill_state,
    initialize_problem_state,
    is_due_for_review,
    is_problem_due_for_review,
    record_attempt,
    time_to_problem_review_seconds,
    time_to_next_review_seconds,
    update_problem_state_schedule,
)
from src.engine.policy import select_next_problem
from src.models.learner import AttemptRecord, AttemptLog

app = typer.Typer()
db = LearnerDB("learner.db")
evaluator = ProblemEvaluator()


@app.command()
def practice(topic: str = typer.Argument(..., help="Topic: arrays, dp, graphs")):
    """Interactive practice session."""
    initial_problems = get_problems_by_topic(topic)
    if not initial_problems:
        typer.echo('{"error": "Invalid topic or no problems found"}')
        return

    # Load or init skill state
    state = db.load_skill_state(topic) or initialize_skill_state(topic)
    now = time.time()
    state, decay_applied = apply_forgetting(state, now)

    assessment = assess_mastery(state)
    starting_mastery = assessment.estimated_mastery
    typer.echo(f"Decay applied: -{decay_applied:.2f} mastery")
    typer.echo(
        f"Next review in {time_to_next_review_seconds(state, now) / 3600:.2f} hours"
    )

    session_attempts = 0
    session_correct = 0
    session_correct_streak = 0
    session_ended = False

    while session_attempts < 5:
        current_problems = get_problems_by_topic(topic)
        if not current_problems:
            typer.echo(f"No problems found for topic: {topic}")
            break
        problem_states = {}
        for p in current_problems:
            ps = db.load_problem_state(p.problem_id)
            if ps is not None:
                problem_states[p.problem_id] = ps
        problem = select_next_problem(
            assessment,
            current_problems,
            topic=topic,
            state=state,
            current_time=time.time(),
            problem_states=problem_states,
        )
        incorrect_attempts = 0

        typer.echo(f"\n--- Problem {session_attempts + 1} of session ---")
        if session_correct_streak >= 3:
            typer.echo(f"🔥 You've solved {session_correct_streak} in a row!")
        typer.echo(f"Problem: {problem.title} (Difficulty: {problem.difficulty}/10)")
        typer.echo(f"Description: {problem.description}")
        typer.echo("Type 'quit' to end session early.\n")

        while True:
            start_time = time.time()
            user_answer = typer.prompt("Your solution")

            if "\n" in user_answer:
                typer.echo("Multi-line input detected. Please enter a single-line answer.")
                continue

            cleaned_answer = user_answer.strip()

            if cleaned_answer == "":
                typer.echo('{"error": "Empty input detected. Please enter an answer or type \'quit\'."}')
                continue

            if cleaned_answer.lower() == "quit":
                typer.echo("Ending session early.")
                session_ended = True
                break

            end_time = time.time()

            time_spent = max(0.0, end_time - start_time)
            is_correct = evaluator.check_solution(problem, user_answer)
            session_attempts += 1

            if is_correct:
                session_correct += 1
                session_correct_streak += 1
                typer.echo("\n✅ Correct!")
            else:
                session_correct_streak = 0
                incorrect_attempts += 1
                typer.echo("\n❌ Incorrect")
                typer.echo(f"💡 Hint: {evaluator.get_hint(problem, incorrect_attempts)}")

            old_mastery = assessment.estimated_mastery

            attempt = AttemptRecord(
                timestamp=end_time,
                problem_id=problem.problem_id,
                success=is_correct,
                time_spent_seconds=time_spent,
                problem_difficulty=problem.difficulty,
                user_id="default_learner",
            )

            state = record_attempt(state, attempt)
            db.save_skill_state(state)
            assessment = assess_mastery(state)

            problem_state = db.load_problem_state(problem.problem_id) or initialize_problem_state(
                problem.problem_id,
                end_time,
            )
            updated_problem_state, quality = update_problem_state_schedule(
                problem_state,
                attempt,
                assessment.confidence,
            )
            db.save_problem_state(updated_problem_state)

            log_entry = AttemptLog(
                timestamp=end_time,
                problem_id=problem.problem_id,
                success=is_correct,
                time_spent_seconds=time_spent,
                quality=quality,
                interval_days=updated_problem_state.interval_days,
                confidence=assessment.confidence,
            )
            db.save_attempt_log(log_entry)

            new_mastery = assessment.estimated_mastery

            typer.echo(f"📈 Mastery: {old_mastery:.1f}% → {new_mastery:.1f}%")
            typer.echo(
                f"Confidence: {assessment.confidence}% | "
                f"Next review in {time_to_next_review_seconds(state, end_time) / 3600:.2f} hours"
            )
            typer.echo(f"Ready to advance: {assessment.ready_to_advance}")

            if is_correct:
                break

        if session_ended:
            break

    accuracy = (session_correct / session_attempts * 100) if session_attempts else 0.0
    final_assessment = assess_mastery(state)
    mastery_delta = final_assessment.estimated_mastery - starting_mastery
    typer.echo("\nSession Summary:")
    typer.echo(f"  Total attempts: {session_attempts}")
    typer.echo(f"  Correct answers: {session_correct}")
    typer.echo(f"  Accuracy: {accuracy:.2f}%")
    typer.echo(f"  Mastery delta: {mastery_delta:+.2f}")


@app.command()
def status(topic: str = typer.Argument(...)):
    """Show learner status for topic."""
    state = db.load_skill_state(topic)
    if not state:
        typer.echo(f"No data for {topic} yet")
        return

    now = time.time()
    effective_state, decay_applied = apply_forgetting(state, now)
    assessment = assess_mastery(effective_state)
    typer.echo(f"\n{topic.upper()} Status:")
    typer.echo(f"  Mastery: {assessment.estimated_mastery}%")
    typer.echo(f"  Confidence: {assessment.confidence}%")
    typer.echo(f"  Attempts: {state.attempt_count}")
    typer.echo(f"  Repetitions: {state.repetitions}")
    typer.echo(f"  Ease factor: {state.ease_factor:.2f}")
    typer.echo(f"  Interval: {state.interval_days:.2f} days")
    typer.echo(f"  Ready to advance: {assessment.ready_to_advance}")
    typer.echo(f"  Next difficulty: {assessment.next_recommended_difficulty}/10")
    typer.echo(f"  Due for review: {is_due_for_review(state, now)}")
    typer.echo(f"  Next review in: {time_to_next_review_seconds(state, now) / 3600:.2f} hours")
    typer.echo(f"  Effective decay now: -{decay_applied:.2f} mastery")


@app.command()
def review():
    """Show per-problem review schedule status with interval and ease-factor."""
    all_problems = load_problems()
    now = time.time()
    review_rows: list[tuple[int, str, str, str, float, float]] = []

    for problem in all_problems:
        problem_state = db.load_problem_state(problem.problem_id) or initialize_problem_state(
            problem.problem_id,
            now,
        )
        due = is_problem_due_for_review(problem_state, problem.difficulty, now)
        hours_to_review = time_to_problem_review_seconds(problem_state, problem.difficulty, now) / 3600
        near_due = hours_to_review <= 6
        status_label = "DUE" if due else ("NEAR-DUE" if near_due else "UPCOMING")
        priority = 0 if due else (1 if near_due else 2)

        review_rows.append(
            (
                priority,
                problem.topic,
                problem.problem_id,
                status_label,
                hours_to_review,
                problem_state.interval_days,
                problem_state.ease_factor,
            )
        )

    if not review_rows:
        typer.echo("No review data available yet")
        return

    review_rows.sort(key=lambda row: (row[0], row[4]))

    typer.echo("\nReview Queue (problem-level due first):")
    for _, topic, problem_id, due_text, next_hours, interval_days, ease_factor in review_rows:
        typer.echo(
            f"- {topic}/{problem_id}: {due_text}, next review in {next_hours:.2f}h, "
            f"interval={interval_days:.2f}d, EF={ease_factor:.2f}"
        )


@app.command()
def recommend():
    """List top 3 next problems based on weakest skills and current DB state."""
    all_problems = load_problems()
    topics = sorted({p.topic for p in all_problems})
    now = time.time()

    topic_rows: list[tuple[float, str, object]] = []
    skill_states = []
    for topic in topics:
        state = db.load_skill_state(topic) or initialize_skill_state(topic)
        effective_state, _ = apply_forgetting(state, now)
        assessment = assess_mastery(effective_state)
        topic_rows.append((assessment.estimated_mastery, topic, assessment))
        skill_states.append(effective_state)

    topic_rows.sort(key=lambda x: x[0])

    recommendations = []
    seen_problem_ids = set()

    for _, topic, assessment in topic_rows:
        if len(recommendations) >= 3:
            break
        topic_problems = [p for p in all_problems if p.topic == topic]
        if not topic_problems:
            continue
        problem_states = {}
        for p in topic_problems:
            ps = db.load_problem_state(p.problem_id)
            if ps is not None:
                problem_states[p.problem_id] = ps

        for _ in range(len(topic_problems)):
            candidate = select_next_problem(
                assessment,
                topic_problems,
                topic=topic,
                state=db.load_skill_state(topic),
                current_time=now,
                problem_states=problem_states,
            )
            if candidate.problem_id not in seen_problem_ids:
                seen_problem_ids.add(candidate.problem_id)
                recommendations.append((topic, assessment, candidate))
                break

    overall = compute_overall_proficiency(skill_states)
    typer.echo(f"Overall proficiency: {overall}%")
    if not recommendations:
        typer.echo("No recommendations available yet")
        return

    typer.echo("Top 3 recommended problems:")
    for idx, (topic, assessment, problem) in enumerate(recommendations[:3], start=1):
        typer.echo(
            f"{idx}. [{topic}] {problem.problem_id} - {problem.title} "
            f"(difficulty={problem.difficulty}, target={assessment.next_recommended_difficulty})"
        )


if __name__ == "__main__":
    app()
