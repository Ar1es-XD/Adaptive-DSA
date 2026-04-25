import json
import sqlite3

from src.models.learner import AttemptRecord, LearnerSkillState


class LearnerDB:
    def __init__(self, db_path: str = "learner.db"):
        self.db_path = db_path
        self._init_schema()

    def _init_schema(self):
        """Create tables if not exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS skill_state (
                    skill_id TEXT PRIMARY KEY,
                    mastery_mu REAL,
                    mastery_variance REAL,
                    last_updated REAL,
                    attempt_count INTEGER,
                    recent_attempts TEXT
                )
            """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS attempts (
                    id INTEGER PRIMARY KEY,
                    skill_id TEXT,
                    timestamp REAL,
                    problem_id TEXT,
                    success INTEGER,
                    time_spent_seconds REAL,
                    problem_difficulty REAL,
                    FOREIGN KEY(skill_id) REFERENCES skill_state(skill_id)
                )
            """
            )
            conn.commit()

    def save_skill_state(self, state: LearnerSkillState):
        """Persist skill state."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO skill_state
                (skill_id, mastery_mu, mastery_variance, last_updated, attempt_count, recent_attempts)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    state.skill_id,
                    state.mastery_mu,
                    state.mastery_variance,
                    state.last_updated,
                    state.attempt_count,
                    json.dumps([a.model_dump() for a in state.recent_attempts]),
                ),
            )
            conn.commit()

    def load_skill_state(self, skill_id: str) -> LearnerSkillState | None:
        """Retrieve skill state."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT * FROM skill_state WHERE skill_id = ?", (skill_id,)).fetchone()

        if not row:
            return None

        attempts_data = json.loads(row[5]) if row[5] else []
        attempts = [AttemptRecord(**a) for a in attempts_data]

        return LearnerSkillState(
            skill_id=row[0],
            mastery_mu=row[1],
            mastery_variance=row[2],
            last_updated=row[3],
            attempt_count=row[4],
            recent_attempts=attempts,
        )
