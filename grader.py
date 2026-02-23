"""
GDPR Cleanup Grader
Validates distributed GDPR cleanup behavior.
"""

import subprocess
import time
import psycopg2
import redis
from pymongo import MongoClient
import requests

USER_ID = "user123"


# ---------------- SETUP ----------------

def run_setup():
    """Seed environment with initial GDPR data."""
    print("Running setup.sh...")

    result = subprocess.run(
        ["bash", "/workspace/setup.sh"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError("setup.sh failed")

    print("Setup completed.")


# ---------------- HELPERS ----------------

def retry(fn, attempts=5):
    """Retry helper for eventual consistency."""
    for _ in range(attempts):
        if fn():
            return True
        time.sleep(3)
    return False


# ---------------- CHECKS ----------------

def auth_deleted():
    """Verify auth-db user removed."""
    conn = psycopg2.connect(
        dbname="auth_db", user="postgres", host="auth-db"
    )
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE id=%s", (USER_ID,))
    result = cur.fetchone()[0]
    conn.close()
    return result == 0


def posts_clean():
    """Verify posts remain but contain no USER_ID."""
    conn = psycopg2.connect(
        dbname="bleat_db", user="postgres", host="bleat-db"
    )
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM posts")
    total_posts = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM posts WHERE author_id=%s",
        (USER_ID,),
    )
    owned = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM posts WHERE content LIKE %s",
        (f"%{USER_ID}%",),
    )
    pii = cur.fetchone()[0]

    conn.close()

    return total_posts > 0 and owned == 0 and pii == 0


def mongo_deleted():
    """Verify MongoDB profile removed."""
    client = MongoClient("mongodb://mongo:27017/")
    db = client["bleater"]
    return db.profiles.count_documents({"user_id": USER_ID}) == 0


def redis_deleted():
    """Verify Redis session removed."""
    r = redis.Redis(host="redis", port=6379)
    return r.get(f"session:{USER_ID}") is None


def avatar_deleted():
    """Verify MinIO avatar deleted."""
    try:
        r = requests.head(
            f"http://minio:9000/avatars/{USER_ID}.png",
            timeout=3,
        )
        return r.status_code == 404
    except requests.exceptions.RequestException:
        return False


def idempotent():
    """Ensure cleanup runs twice safely."""
    r1 = subprocess.run(["bash", "/workspace/solution.sh"])
    r2 = subprocess.run(["bash", "/workspace/solution.sh"])

    if r1.returncode != 0 or r2.returncode != 0:
        return False

    return all([
        auth_deleted(),
        posts_clean(),
        mongo_deleted(),
        redis_deleted(),
        avatar_deleted(),
    ])


# ---------------- GRADE ----------------

def grade():
    run_setup()

    print("Waiting for convergence...")
    time.sleep(8)

    checks = {
        "auth_deleted": retry(auth_deleted),
        "posts_clean": retry(posts_clean),
        "mongo_deleted": retry(mongo_deleted),
        "redis_deleted": retry(redis_deleted),
        "avatar_deleted": retry(avatar_deleted),
        "idempotent": idempotent(),
    }

    print(checks)

    if all(checks.values()):
        print("PASS")
        exit(0)
    else:
        print("FAIL")
        exit(1)


if __name__ == "__main__":
    grade()