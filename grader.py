#!/usr/bin/env python3
"""
GDPR Cleanup Grader

Verifies removal of user123 PII across all systems.
"""

import subprocess
import time
from apex_arena._types import GradingResult

USER_ID = "user123"


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def sql_count(cmd):
    """Return integer count from psql output."""
    r = run(cmd)
    try:
        return int(r.stdout.strip())
    except:
        return -1


def auth_deleted():
    """Verify auth-db user removed."""
    return sql_count(
        f"psql -h auth-db -U postgres -d auth_db "
        f"-t -A -c \"SELECT COUNT(*) FROM users WHERE id='{USER_ID}';\""
    ) == 0


def posts_clean():
    """Verify posts remain but contain no USER_ID."""
    owned = sql_count(
        f"psql -h bleat-db -U postgres -d bleat_db "
        f"-t -A -c \"SELECT COUNT(*) FROM posts WHERE author_id='{USER_ID}';\""
    )

    pii = sql_count(
        f"psql -h bleat-db -U postgres -d bleat_db "
        f"-t -A -c \"SELECT COUNT(*) FROM posts WHERE content LIKE '%{USER_ID}%';\""
    )

    total = sql_count(
        "psql -h bleat-db -U postgres -d bleat_db "
        "-t -A -c \"SELECT COUNT(*) FROM posts;\""
    )

    return total > 0 and owned == 0 and pii == 0


def mongo_deleted():
    """Verify Mongo profile removed."""
    r = run(
        "mongosh --host mongo bleater --quiet "
        f"--eval \"db.profiles.countDocuments({{user_id:'{USER_ID}'}})\""
    )
    return r.stdout.strip() == "0"


def redis_deleted():
    """Verify Redis session removed."""
    r = run(f"redis-cli -h redis GET session:{USER_ID}")
    return "(nil)" in r.stdout


def avatar_deleted():
    """Verify MinIO avatar deleted."""
    r = run(
        f"mc stat minio/avatars/{USER_ID}.png"
    )
    return r.returncode != 0


def grade():
    print("Running setup...")
    run("bash /workspace/setup.sh")
    time.sleep(8)

    print("Running solution...")
    run("bash /workspace/solution.sh")

    checks = [
        auth_deleted(),
        posts_clean(),
        mongo_deleted(),
        redis_deleted(),
        avatar_deleted(),
    ]

    return GradingResult(score=1.0 if all(checks) else 0.0)


if __name__ == "__main__":
    print(grade())