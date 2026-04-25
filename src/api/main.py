from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.services.tutor_service import (
    get_analytics_summary,
    get_recommend,
    get_review,
    get_status,
    start_problem,
    start_session,
    submit_answer,
)


class StartPracticeRequest(BaseModel):
    topic: str


class SubmitPracticeRequest(BaseModel):
    problem_id: str
    answer: str


class PracticeProblemRequest(BaseModel):
    problem_id: str


app = FastAPI(title="Adaptive DSA Tutor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/practice/start")
def practice_start(req: StartPracticeRequest):
    return start_session(req.topic)


@app.post("/practice/submit")
def practice_submit(req: SubmitPracticeRequest):
    return submit_answer(req.problem_id, req.answer)


@app.post("/practice/problem")
def practice_problem(req: PracticeProblemRequest):
    return start_problem(req.problem_id)


@app.get("/status/{topic}")
def status(topic: str):
    return get_status(topic)


@app.get("/review")
def review():
    return get_review()


@app.get("/recommend")
def recommend():
    return get_recommend()


@app.get("/analytics/summary")
def analytics_summary():
    return get_analytics_summary()
