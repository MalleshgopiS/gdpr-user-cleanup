import subprocess
import json
from apex_arena._types import GradingResult

USER_ID = "user123" [cite: 2]

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def grade(transcript: str) -> GradingResult:
    feedback = []
    scores = {}

    # 1. Check Auth Record Deletion
    r = run(f"psql -h auth-db -U postgres -d auth_db -t -c \"SELECT COUNT(*) FROM users WHERE id='{USER_ID}';\"")
    auth_ok = r.stdout.strip() == "0"
    feedback.append(f"{'✓' if auth_ok else '✗'} Auth record deleted")
    scores["auth_deleted"] = 1.0 if auth_ok else 0.0 [cite: 2]

    # 2. Check MongoDB Profile Deletion
    r = run(f"mongosh --host mongo --quiet --eval \"db=db.getSiblingDB('bleater'); print(db.profiles.countDocuments({{user_id:'{USER_ID}'}}));\"")
    mongo_ok = r.stdout.strip() == "0"
    feedback.append(f"{'✓' if mongo_ok else '✗'} MongoDB profile removed")
    scores["mongo_deleted"] = 1.0 if mongo_ok else 0.0 [cite: 2]

    # 3. Check Post Anonymization
    r = run(f"psql -h bleat-db -U postgres -d bleat_db -t -c \"SELECT COUNT(*) FROM posts WHERE author_id='{USER_ID}' OR content LIKE '%{USER_ID}%';\"")
    posts_ok = r.stdout.strip() == "0"
    feedback.append(f"{'✓' if posts_ok else '✗'} Posts anonymized")
    scores["posts_anonymized"] = 1.0 if posts_ok else 0.0 [cite: 2]

    # 4. Check Redis Session Deletion
    r = run(f"redis-cli -h redis EXISTS session:{USER_ID}")
    redis_ok = r.stdout.strip() == "0"
    feedback.append(f"{'✓' if redis_ok else '✗'} Redis session cleared")
    scores["redis_deleted"] = 1.0 if redis_ok else 0.0 [cite: 2]

    total_score = sum(scores.values()) / len(scores)

    return GradingResult(
        score=total_score,
        subscores=scores,
        weights={k: 1.0 for k in scores.keys()},
        feedback=" | ".join(feedback)
    )