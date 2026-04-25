import json
import sqlite3
import time

from src.models.learner import AttemptRecord, LearnerSkillState, AttemptLog
from src.models.problem_state import ProblemState


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
                    last_seen_timestamp REAL,
                    repetitions INTEGER,
                    ease_factor REAL,
                    interval_days REAL,
                    review_interval_seconds REAL,
                    attempt_count INTEGER,
                    recent_attempts TEXT
                )
            """
            )
            self._ensure_skill_state_column(conn, "last_seen_timestamp", "REAL")
            self._ensure_skill_state_column(conn, "repetitions", "INTEGER")
            self._ensure_skill_state_column(conn, "ease_factor", "REAL")
            self._ensure_skill_state_column(conn, "interval_days", "REAL")
            self._ensure_skill_state_column(conn, "review_interval_seconds", "REAL")
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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS problem_state (
                    problem_id TEXT PRIMARY KEY,
                    repetitions INTEGER,
                    ease_factor REAL,
                    interval_days REAL,
                    last_seen_timestamp REAL
                )
            """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS attempt_logs (
                    id INTEGER PRIMARY KEY,
                    timestamp REAL,
                    problem_id TEXT,
                    success INTEGER,
                    time_spent_seconds REAL,
                    quality INTEGER,
                    interval_days REAL,
                    confidence REAL
                )
                """
            )
            conn.commit()

    def _ensure_skill_state_column(self, conn: sqlite3.Connection, name: str, col_type: str) -> None:
        existing_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(skill_state)").fetchall()
        }
        if name not in existing_columns:
            conn.execute(f"ALTER TABLE skill_state ADD COLUMN {name} {col_type}")

    def save_skill_state(self, state: LearnerSkillState):
        """Persist skill state."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO skill_state
                (skill_id, mastery_mu, mastery_variance, last_updated, last_seen_timestamp,
                 repetitions, ease_factor, interval_days, review_interval_seconds,
                 attempt_count, recent_attempts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    state.skill_id,
                    state.mastery_mu,
                    state.mastery_variance,
                    state.last_updated,
                    state.last_seen_timestamp,
                    state.repetitions,
                    state.ease_factor,
                    state.interval_days,
                    state.review_interval_seconds,
                    state.attempt_count,
                    json.dumps([a.model_dump() for a in state.recent_attempts]),
                ),
            )
            conn.commit()

    def load_skill_state(self, skill_id: str) -> LearnerSkillState | None:
        """Retrieve skill state."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT
                    skill_id,
                    mastery_mu,
                    mastery_variance,
                    last_updated,
                    COALESCE(last_seen_timestamp, last_updated),
                    COALESCE(repetitions, 0),
                    COALESCE(ease_factor, 2.5),
                    COALESCE(interval_days, 1.0),
                    COALESCE(review_interval_seconds, 86400.0),
                    attempt_count,
                    recent_attempts
                FROM skill_state
                WHERE skill_id = ?
                """,
                (skill_id,),
            ).fetchone()

        if not row:
            return None

        attempts_data = json.loads(row[10]) if row[10] else []
        attempts = [AttemptRecord(**a) for a in attempts_data]

        return LearnerSkillState(
            skill_id=row[0],
            mastery_mu=row[1],
            mastery_variance=row[2],
            last_updated=row[3],
            last_seen_timestamp=row[4] if row[4] is not None else time.time(),
            repetitions=row[5] if row[5] is not None else 0,
            ease_factor=row[6] if row[6] is not None else 2.5,
            interval_days=row[7] if row[7] is not None else 1.0,
            review_interval_seconds=row[8] if row[8] is not None else 86400.0,
            attempt_count=row[9],
            recent_attempts=attempts,
        )

    def save_problem_state(self, state: ProblemState):
        """Persist per-problem scheduling state."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO problem_state
                (problem_id, repetitions, ease_factor, interval_days, last_seen_timestamp)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    state.problem_id,
                    state.repetitions,
                    state.ease_factor,
                    state.interval_days,
                    state.last_seen_timestamp,
                ),
            )
            conn.commit()

    def load_problem_state(self, problem_id: str) -> ProblemState | None:
        """Retrieve one problem scheduling state."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT
                    problem_id,
                    COALESCE(repetitions, 0),
                    COALESCE(ease_factor, 2.5),
                    COALESCE(interval_days, 1.0),
                    last_seen_timestamp
                FROM problem_state
                WHERE problem_id = ?
                """,
                (problem_id,),
            ).fetchone()

        if not row:
            return None

        return ProblemState(
            problem_id=row[0],
            repetitions=row[1] if row[1] is not None else 0,
            ease_factor=row[2] if row[2] is not None else 2.5,
            interval_days=row[3] if row[3] is not None else 1.0,
            last_seen_timestamp=row[4] if row[4] is not None else time.time(),
        )

    def save_attempt_log(self, log: AttemptLog):
        """Persist detailed attempt log."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO attempt_logs
                (timestamp, problem_id, success, time_spent_seconds, quality, interval_days, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    log.timestamp,
                    log.problem_id,
                    1 if log.success else 0,
                    log.time_spent_seconds,
                    log.quality,
                    log.interval_days,
                    log.confidence,
                ),
            )
            conn.commit()

    def get_attempt_summary(self) -> dict:
        """Return aggregate metrics from attempt logs."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_attempts,
                    COALESCE(AVG(success), 0.0) AS accuracy,
                    COALESCE(AVG(time_spent_seconds), 0.0) AS avg_time
                FROM attempt_logs
                """
            ).fetchone()

        return {
            "total_attempts": int(row[0] or 0),
            "accuracy": round(float(row[1] or 0.0), 2),
            "avg_time": round(float(row[2] or 0.0), 2),
        }
