#!/usr/bin/env python3
import subprocess
import time
from apex_arena._types import GradingResult

USER_ID = "user123"


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def auth_deleted():
    r = run(
        f"psql -h auth-db -U postgres -d auth_db "
        f"-t -c \"SELECT COUNT(*) FROM users WHERE id='{USER_ID}';\""
    )
    return "0" in r.stdout


def posts_clean():
    r = run(
        f"psql -h bleat-db -U postgres -d bleat_db "
        f"-t -c \"SELECT COUNT(*) FROM posts "
        f"WHERE author_id='{USER_ID}' OR content LIKE '%{USER_ID}%';\""
    )
    return "0" in r.stdout


def mongo_deleted():
    r = run(
        "mongosh --host mongo bleater --quiet "
        f"--eval \"db.profiles.countDocuments({{user_id:'{USER_ID}'}})\""
    )
    return "0" in r.stdout


def redis_deleted():
    r = run(f"redis-cli -h redis GET session:{USER_ID}")
    return "(nil)" in r.stdout


def grade():
    print("Running setup...")
    run("bash /workspace/setup.sh")
    time.sleep(5)

    print("Running solution...")
    run("bash /workspace/solution.sh")

    checks = [
        auth_deleted(),
        posts_clean(),
        mongo_deleted(),
        redis_deleted(),
    ]

    return GradingResult(score=1.0 if all(checks) else 0.0)


if __name__ == "__main__":
    print(grade())