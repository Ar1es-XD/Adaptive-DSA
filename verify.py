import time
import sqlite3
import subprocess

def run_practice(inputs):
    proc = subprocess.Popen(
        ["venv/bin/python", "main.py", "practice", "arrays"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    out, err = proc.communicate(input=inputs)
    return out

def get_db_stats():
    conn = sqlite3.connect("learner.db")
    cursor = conn.cursor()
    cursor.execute("SELECT problem_id, repetitions, interval_days, last_seen_timestamp FROM problem_state")
    rows = cursor.fetchall()
    conn.close()
    return rows

print("--- Test 1 & 2 & 3: Progression, Reset, Independence ---")
subprocess.run(["rm", "-f", "learner.db"])

print("Simulating Attempt 1 (array_001 correct, array_002 incorrect)")
run_practice("indices 0 and 1\nquit\n") 
# wait, the first problem is array_001. "indices 0 and 1" is expected output for Two sum? 
# let's look at problems.json to get expected output
