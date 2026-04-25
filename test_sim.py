import subprocess
import sqlite3
import json

# Backup problems
with open('src/data/problems.json', 'r') as f:
    orig_problems = json.load(f)

# Run test 1 & 2
with open('src/data/problems.json', 'w') as f:
    json.dump([p for p in orig_problems if p['problem_id'] == 'array_001'], f)

subprocess.run(["rm", "-f", "learner.db"])

print("--- Test 1 ---\nAttempt 1 (correct):")
subprocess.run(["venv/bin/python", "main.py", "practice", "arrays"], input="indices 0 and 1\nquit\n", text=True, stdout=subprocess.DEVNULL)
conn = sqlite3.connect("learner.db")
c = conn.cursor()
print(c.execute("SELECT problem_id, repetitions, interval_days FROM problem_state").fetchall())

print("Attempt 2 (correct):")
subprocess.run(["venv/bin/python", "main.py", "practice", "arrays"], input="indices 0 and 1\nquit\n", text=True, stdout=subprocess.DEVNULL)
print(c.execute("SELECT problem_id, repetitions, interval_days FROM problem_state").fetchall())

print("Attempt 3 (correct):")
subprocess.run(["venv/bin/python", "main.py", "practice", "arrays"], input="indices 0 and 1\nquit\n", text=True, stdout=subprocess.DEVNULL)
print(c.execute("SELECT problem_id, repetitions, interval_days FROM problem_state").fetchall())

print("\n--- Test 2 ---\nAttempt 4 (failure):")
subprocess.run(["venv/bin/python", "main.py", "practice", "arrays"], input="wrong\nquit\n", text=True, stdout=subprocess.DEVNULL)
print(c.execute("SELECT problem_id, repetitions, interval_days FROM problem_state").fetchall())

print("\n--- Test 3 ---\nRestoring problems...")
with open('src/data/problems.json', 'w') as f:
    json.dump([p for p in orig_problems if p['problem_id'] in ('array_001', 'array_002')], f)

subprocess.run(["rm", "-f", "learner.db"])
# run once and answer array_001 correct, array_002 incorrect.
# since random, we just supply both answers:
subprocess.run(["venv/bin/python", "main.py", "practice", "arrays"], input="indices 0 and 1\nwrong\nwrong\nwrong\nquit\n", text=True, stdout=subprocess.DEVNULL)
subprocess.run(["venv/bin/python", "main.py", "practice", "arrays"], input="wrong\nwrong\nindices 0 and 1\nquit\n", text=True, stdout=subprocess.DEVNULL)

print("DB state:")
for row in c.execute("SELECT problem_id, repetitions, interval_days FROM problem_state"):
    print(row)
    
print("\n--- Test 4 & 5 ---\nForcing array_002 to be due...")
c.execute("UPDATE problem_state SET last_seen_timestamp = last_seen_timestamp - 90000 WHERE problem_id = 'array_002'")
conn.commit()

print("\nRun main.py review:")
subprocess.run(["venv/bin/python", "main.py", "review"])

# Restore original
with open('src/data/problems.json', 'w') as f:
    json.dump(orig_problems, f)
