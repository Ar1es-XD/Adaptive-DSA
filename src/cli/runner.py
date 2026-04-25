import time

import typer

from src.data.loader import get_problems_by_topic, load_problems
from src.db.storage import LearnerDB
from src.engine.evaluator import ProblemEvaluator
from src.engine.learner_model import (
    apply_forgetting,
    assess_mastery,
    initialize_skill_state,
    is_due_for_review,
    record_attempt,
    time_to_next_review_seconds,
)
from src.engine.policy import select_next_problem
from src.models.learner import AttemptRecord

app = typer.Typer()
db = LearnerDB("learner.db")
evaluator = ProblemEvaluator()


@app.command()
def practice(topic: str = typer.Argument(..., help="Topic: arrays, dp, graphs")):
    """Interactive practice session."""
    initial_problems = get_problems_by_topic(topic)
    if not initial_problems:
        typer.echo(f"No problems found for topic: {topic}")
        return

    # Load or init skill state
    state = db.load_skill_state(topic) or initialize_skill_state(topic)
    now = time.time()
    state, decay_applied = apply_forgetting(state, now)
    db.save_skill_state(state)

    assessment = assess_mastery(state)
    starting_mastery = assessment.estimated_mastery
    typer.echo(f"Decay applied: -{decay_applied:.2f} mastery")
    typer.echo(
        f"Next review in {time_to_next_review_seconds(state, now) / 3600:.2f} hours"
    )

    session_attempts = 0
    session_correct = 0
    session_ended = False

    while session_attempts < 5:
        current_problems = get_problems_by_topic(topic)
        if not current_problems:
            typer.echo(f"No problems found for topic: {topic}")
            break
        problem = select_next_problem(assessment, current_problems, state=state, current_time=time.time())
        incorrect_attempts = 0

        typer.echo(f"\nProblem: {problem.title} (Difficulty: {problem.difficulty}/10)")
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
                typer.echo("Empty input detected. Please enter an answer or type 'quit'.")
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
                typer.echo("\nCorrect!")
            else:
                incorrect_attempts += 1
                typer.echo("\nIncorrect")
                typer.echo(f"Hint: {evaluator.get_hint(problem, incorrect_attempts)}")

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

            typer.echo(
                f"Mastery: {assessment.estimated_mastery}% "
                f"(Confidence: {assessment.confidence}%)"
            )
            typer.echo(f"Ready to advance: {assessment.ready_to_advance}")
            typer.echo(
                f"Next review in {time_to_next_review_seconds(state, end_time) / 3600:.2f} hours"
            )

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

    assessment = assess_mastery(state)
    now = time.time()
    typer.echo(f"\n{topic.upper()} Status:")
    typer.echo(f"  Mastery: {assessment.estimated_mastery}%")
    typer.echo(f"  Confidence: {assessment.confidence}%")
    typer.echo(f"  Attempts: {state.attempt_count}")
    typer.echo(f"  Ready to advance: {assessment.ready_to_advance}")
    typer.echo(f"  Next difficulty: {assessment.next_recommended_difficulty}/10")
    typer.echo(f"  Due for review: {is_due_for_review(state, now)}")
    typer.echo(f"  Next review in: {time_to_next_review_seconds(state, now) / 3600:.2f} hours")


@app.command()
def review():
    """Show skills and problems due for review, prioritizing weak skills."""
    all_problems = load_problems()
    topics = sorted({p.topic for p in all_problems})
    now = time.time()
    review_rows: list[tuple[str, float, bool, float, str]] = []

    for topic in topics:
        topic_problems = [p for p in all_problems if p.topic == topic]
        if not topic_problems:
            continue

        state = db.load_skill_state(topic) or initialize_skill_state(topic)
        state, decay_applied = apply_forgetting(state, now)
        db.save_skill_state(state)

        assessment = assess_mastery(state)
        due = is_due_for_review(state, now)
        next_problem = select_next_problem(assessment, topic_problems, state=state, current_time=now)
        review_rows.append(
            (
                topic,
                assessment.estimated_mastery,
                due,
                time_to_next_review_seconds(state, now) / 3600,
                next_problem.title,
            )
        )

        typer.echo(f"Decay applied for {topic}: -{decay_applied:.2f} mastery")

    if not review_rows:
        typer.echo("No review data available yet")
        return

    review_rows.sort(key=lambda row: (not row[2], row[1]))

    typer.echo("\nReview Queue (due first, weaker skills first):")
    for topic, mastery, due, next_hours, next_problem in review_rows:
        due_text = "DUE" if due else "UPCOMING"
        typer.echo(
            f"- {topic}: {due_text}, mastery={mastery:.2f}, "
            f"next review in {next_hours:.2f}h, next problem='{next_problem}'"
        )


if __name__ == "__main__":
    app()
