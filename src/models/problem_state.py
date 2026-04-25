from pydantic import BaseModel

class ProblemState(BaseModel):
    problem_id: str
    repetitions: int = 0
    ease_factor: float = 2.5
    interval_days: float = 1.0
    last_seen_timestamp: float
