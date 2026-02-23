"""
GDPR Cleanup Grader

Validates that the agent implemented a correct
Right-to-be-Forgotten pipeline across distributed services.
"""

import subprocess
import time
import psycopg2
import redis
from pymongo import MongoClient
import requests

USER_ID = "user123"


def retry(fn, attempts=5):
    """Retry helper for eventual consistency."""
    for _ in range(attempts):
        if fn():
            return True
        time.sleep(3)
    return False


# ---------------- AUTH ----------------
def auth_deleted():
    """Verify auth-db user removed."""
    conn = psycopg2.connect(
        dbname="auth_db", user="postgres", host="auth-db"
    )
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE id=%s", (USER_ID,))
    count = cur.fetchone()[0]
    conn.close()
    return count == 0


# ---------------- POSTS ----------------
def posts_anonymized():
    """Verify posts no longer contain user identity or PII."""
    conn = psycopg2.connect(
        dbname="bleat_db", user="postgres", host="bleat-db"
    )
    cur = conn.cursor()

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
    return owned == 0 and pii == 0


# ---------------- MONGO ----------------
def mongo_deleted():
    """Verify Mongo profile removed."""
    client = MongoClient("mongodb://mongo:27017/")
    db = client["bleater"]
    return db.profiles.count_documents({"user_id": USER_ID}) == 0


# ---------------- REDIS ----------------
def redis_deleted():
    """Verify Redis session removed."""
    r = redis.Redis(host="redis", port=6379)
    return r.get(f"session:{USER_ID}") is None


# ---------------- MINIO ----------------
def avatar_deleted():
    """Verify avatar object removed from MinIO."""
    try:
        r = requests.head(
            f"http://minio:9000/avatars/{USER_ID}.png",
            timeout=3,
        )
        return r.status_code == 404
    except:
        return True


# ---------------- IDEMPOTENCY ----------------
def idempotent():
    """Run solution twice and ensure stable state."""
    r1 = subprocess.run(["bash", "/workspace/run.sh"])
    r2 = subprocess.run(["bash", "/workspace/run.sh"])

    if r1.returncode != 0 or r2.returncode != 0:
        return False

    return all([
        auth_deleted(),
        posts_anonymized(),
        mongo_deleted(),
        redis_deleted(),
        avatar_deleted(),
    ])


# ---------------- MAIN ----------------
def grade():
    print("Waiting for convergence...")
    time.sleep(8)

    checks = {
        "auth_deleted": retry(auth_deleted),
        "posts_anonymized": retry(posts_anonymized),
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