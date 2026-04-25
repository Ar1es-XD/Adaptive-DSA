import subprocess
import sqlite3

# Test 4 & 5: Force Due
print("\n--- Test 4 & 5 ---")
subprocess.run(["rm", "-f", "learner.db"])

conn = sqlite3.connect("learner.db")
c = conn.cursor()

# We know the schema natively creates tables on first run via LearnerDB
from src.db.storage import LearnerDB
from src.models.problem_state import ProblemState
import time

db = LearnerDB("learner.db")
now = time.time()
db.save_problem_state(ProblemState(
    problem_id="array_001",
    repetitions=3, ease_factor=2.5, interval_days=21.6,
    last_seen_timestamp=now
))

db.save_problem_state(ProblemState(
    problem_id="array_002",
    repetitions=0, ease_factor=2.5, interval_days=1.0,
    last_seen_timestamp=now - 90000 # More than 1 day ago (1.0 days * 86400 = 86400 seconds)
))

print("Run main.py review:")
subprocess.run(["venv/bin/python", "main.py", "review"])

print("\n--- Test 3 ---\nChecking Independence")
print("We have two independent problem states:")
for row in c.execute("SELECT problem_id, repetitions, interval_days FROM problem_state"):
    print(row)
