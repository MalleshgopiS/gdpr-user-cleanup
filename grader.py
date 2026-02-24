"""
Grader for GDPR "Right to be Forgotten" task.
"""
import subprocess
from apex_arena._types import GradingResult

USER_ID = "user123"
SOLUTION_PATH = "/workspace/solution.sh"

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def grade(transcript: str) -> GradingResult:
    feedback = []
    scores = {}

    # --- Idempotency Check ---
    run_1 = run(f"bash {SOLUTION_PATH}")
    run_2 = run(f"bash {SOLUTION_PATH}")
    
    idempotency_ok = (run_1.returncode == 0) and (run_2.returncode == 0)
    scores["idempotency"] = 1.0 if idempotency_ok else 0.0
    feedback.append(f"{'✓' if idempotency_ok else '✗'} Script executed successfully and is idempotent")

    # --- 1. Check Auth Record Deletion ---
    r = run(f"psql -h auth-db -U postgres -d auth_db -t -c \"SELECT COUNT(*) FROM users WHERE id='{USER_ID}';\"")
    auth_ok = r.stdout.strip() == "0"
    scores["auth_deleted"] = 1.0 if auth_ok else 0.0
    feedback.append(f"{'✓' if auth_ok else '✗'} Auth record deleted")

    # --- 2. Check MongoDB Profile Deletion ---
    r = run(f"mongosh --host mongo --quiet --eval \"db=db.getSiblingDB('bleater'); print(db.profiles.countDocuments({{user_id:'{USER_ID}'}}));\"")
    mongo_ok = r.stdout.strip() == "0"
    scores["mongo_deleted"] = 1.0 if mongo_ok else 0.0
    feedback.append(f"{'✓' if mongo_ok else '✗'} MongoDB profile removed")

    # --- 3. Check Post Anonymization ---
    # Separately verify authorship change AND global content redaction
    r_author_gone = run(f"psql -h bleat-db -U postgres -d bleat_db -t -c \"SELECT COUNT(*) FROM posts WHERE author_id='{USER_ID}';\"")
    r_author_replaced = run(f"psql -h bleat-db -U postgres -d bleat_db -t -c \"SELECT COUNT(*) FROM posts WHERE author_id='deleted_user';\"")
    
    r_content_gone = run(f"psql -h bleat-db -U postgres -d bleat_db -t -c \"SELECT COUNT(*) FROM posts WHERE content LIKE '%{USER_ID}%';\"")
    r_content_redacted = run(f"psql -h bleat-db -U postgres -d bleat_db -t -c \"SELECT COUNT(*) FROM posts WHERE content LIKE '%[REDACTED]%';\"")
    
    try:
        posts_ok = (r_author_gone.stdout.strip() == "0" and 
                    r_content_gone.stdout.strip() == "0" and 
                    int(r_author_replaced.stdout.strip()) > 0 and
                    int(r_content_redacted.stdout.strip()) > 0)
    except ValueError:
        posts_ok = False
        
    scores["posts_anonymized"] = 1.0 if posts_ok else 0.0
    feedback.append(f"{'✓' if posts_ok else '✗'} Posts anonymized globally")

    # --- 4. Check External Stores (Redis & MinIO) ---
    redis_r = run(f"redis-cli -h redis EXISTS session:{USER_ID}")
    
    alias_setup = run("mc alias set local http://minio:9000 minioadmin minioadmin")
    if alias_setup.returncode != 0:
        minio_ok = False
    else:
        minio_r = run(f"mc ls local/avatars/{USER_ID}.png")
        minio_ok = (minio_r.returncode != 0)
        
    external_ok = (redis_r.stdout.strip() == "0") and minio_ok
    scores["external_cleanup"] = 1.0 if external_ok else 0.0
    feedback.append(f"{'✓' if external_ok else '✗'} Redis session and MinIO avatar cleaned")

    # --- Final Scoring ---
    total_score = sum(scores.values()) / len(scores)

    return GradingResult(
        score=total_score,
        subscores=scores,
        weights={k: 1.0 for k in scores.keys()},
        feedback=" | ".join(feedback)
    )