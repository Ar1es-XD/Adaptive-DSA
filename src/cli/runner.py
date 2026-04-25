import time

import typer

from src.data.loader import get_problems_by_topic
from src.db.storage import LearnerDB
from src.engine.evaluator import ProblemEvaluator
from src.engine.learner_model import assess_mastery, initialize_skill_state, record_attempt
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
    assessment = assess_mastery(state)
    starting_mastery = assessment.estimated_mastery

    session_attempts = 0
    session_correct = 0

    for _ in range(5):
        current_problems = get_problems_by_topic(topic)
        if not current_problems:
            typer.echo(f"No problems found for topic: {topic}")
            break
        problem = select_next_problem(assessment, current_problems)
        incorrect_attempts = 0

        typer.echo(f"\nProblem: {problem.title} (Difficulty: {problem.difficulty}/10)")
        typer.echo(f"Description: {problem.description}")
        typer.echo("Type 'quit' to end session early.\n")

        while True:
            start_time = time.time()
            user_answer = typer.prompt("Your solution")
            end_time = time.time()

            if user_answer.strip().lower() == "quit":
                typer.echo("Ending session early.")
                accuracy = (session_correct / session_attempts * 100) if session_attempts else 0.0
                final_assessment = assess_mastery(state)
                mastery_delta = final_assessment.estimated_mastery - starting_mastery
                typer.echo("\nSession Summary:")
                typer.echo(f"  Total attempts: {session_attempts}")
                typer.echo(f"  Correct answers: {session_correct}")
                typer.echo(f"  Accuracy: {accuracy:.2f}%")
                typer.echo(f"  Mastery delta: {mastery_delta:+.2f}")
                return

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

            if is_correct:
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
    typer.echo(f"\n{topic.upper()} Status:")
    typer.echo(f"  Mastery: {assessment.estimated_mastery}%")
    typer.echo(f"  Confidence: {assessment.confidence}%")
    typer.echo(f"  Attempts: {state.attempt_count}")
    typer.echo(f"  Ready to advance: {assessment.ready_to_advance}")
    typer.echo(f"  Next difficulty: {assessment.next_recommended_difficulty}/10")


if __name__ == "__main__":
    app()
