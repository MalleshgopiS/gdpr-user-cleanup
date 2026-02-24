import subprocess
import os
from apex_arena._types import GradingResult

USER_ID = "user123"
SOLUTION_PATH = "/workspace/solution.sh"

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def grade(transcript: str) -> GradingResult:
    feedback = []
    scores = {}

    # Run solution the first time
    run_1 = run(f"bash {SOLUTION_PATH}")
    
    # Run solution a second time to test Idempotency
    run_2 = run(f"bash {SOLUTION_PATH}")
    idempotency_ok = run_2.returncode == 0
    scores["idempotency"] = 1.0 if idempotency_ok else 0.0
    feedback.append(f"{'✓' if idempotency_ok else '✗'} Idempotency")

    # 1. Check Auth Deletion
    r = run(f"psql -h auth-db -U postgres -d auth_db -t -c \"SELECT COUNT(*) FROM users WHERE id='{USER_ID}';\"")
    auth_ok = r.stdout.strip() == "0"
    scores["auth_deleted"] = 1.0 if auth_ok else 0.0
    feedback.append(f"{'✓' if auth_ok else '✗'} Auth record deleted")

    # 2. Check MongoDB Profile Deletion
    r = run(f"mongosh --host mongo --quiet --eval \"db=db.getSiblingDB('bleater'); print(db.profiles.countDocuments({{user_id:'{USER_ID}'}}));\"")
    mongo_ok = r.stdout.strip() == "0"
    scores["mongo_deleted"] = 1.0 if mongo_ok else 0.0
    feedback.append(f"{'✓' if mongo_ok else '✗'} MongoDB profile removed")

    # 3. Check Post Anonymization
    r_author = run(f"psql -h bleat-db -U postgres -d bleat_db -t -c \"SELECT COUNT(*) FROM posts WHERE author_id='{USER_ID}';\"")
    r_content = run(f"psql -h bleat-db -U postgres -d bleat_db -t -c \"SELECT COUNT(*) FROM posts WHERE content LIKE '%{USER_ID}%';\"")
    posts_ok = r_author.stdout.strip() == "0" and r_content.stdout.strip() == "0"
    scores["posts_anonymized"] = 1.0 if posts_ok else 0.0
    feedback.append(f"{'✓' if posts_ok else '✗'} Posts anonymized")

    # 4. Check Redis/MinIO Cleanup
    redis_r = run(f"redis-cli -h redis EXISTS session:{USER_ID}")
    run("mc alias set local http://minio:9000 minioadmin minioadmin")
    minio_r = run(f"mc ls local/avatars/{USER_ID}.png")
    
    cleanup_ok = redis_r.stdout.strip() == "0" and minio_r.returncode != 0
    scores["cleanup_external"] = 1.0 if cleanup_ok else 0.0
    feedback.append(f"{'✓' if cleanup_ok else '✗'} External stores cleaned")

    total_score = sum(scores.values()) / len(scores)

    return GradingResult(
        score=total_score,
        subscores=scores,
        weights={k: 1.0 for k in scores.keys()},
        feedback=" | ".join(feedback)
    )