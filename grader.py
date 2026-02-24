import subprocess
from apex_arena._types import GradingResult

USER_ID = "user123"

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def grade(transcript: str) -> GradingResult:
    feedback = []
    scores = {}

    # 1. Check Auth Record Deletion
    r_auth = run(f"psql -h auth-db -U postgres -d auth_db -t -c \"SELECT COUNT(*) FROM users WHERE id='{USER_ID}';\"")
    auth_deleted = r_auth.stdout.strip() == "0"
    scores["auth_cleanup"] = 1.0 if auth_deleted else 0.0
    feedback.append(f"{'✓' if auth_deleted else '✗'} Auth record")

    # 2. Check Posts Anonymization
    r_posts = run(f"psql -h bleat-db -U postgres -d bleat_db -t -c \"SELECT COUNT(*) FROM posts WHERE author_id='{USER_ID}' OR content LIKE '%{USER_ID}%';\"")
    posts_clean = r_posts.stdout.strip() == "0"
    scores["posts_anonymized"] = 1.0 if posts_clean else 0.0
    feedback.append(f"{'✓' if posts_clean else '✗'} Posts anonymized")

    # 3. Check MongoDB Profile Deletion
    r_mongo = run(f"mongosh --host mongo --quiet --eval \"db=db.getSiblingDB('bleater'); print(db.profiles.countDocuments({{user_id:'{USER_ID}'}}));\"")
    mongo_deleted = r_mongo.stdout.strip() == "0"
    scores["mongo_cleanup"] = 1.0 if mongo_deleted else 0.0
    feedback.append(f"{'✓' if mongo_deleted else '✗'} Mongo profile")

    # 4. Check Redis Session Deletion
    r_redis = run(f"redis-cli -h redis EXISTS session:{USER_ID}")
    redis_deleted = r_redis.stdout.strip() == "0"
    scores["redis_cleanup"] = 1.0 if redis_deleted else 0.0
    feedback.append(f"{'✓' if redis_deleted else '✗'} Redis session")

    # 5. Check MinIO Avatar Deletion
    run("mc alias set local http://minio:9000 minioadmin minioadmin")
    r_minio = run(f"mc ls local/avatars/{USER_ID}.png")
    minio_deleted = r_minio.returncode != 0 # Return code non-zero means file not found
    scores["minio_cleanup"] = 1.0 if minio_deleted else 0.0
    feedback.append(f"{'✓' if minio_deleted else '✗'} MinIO avatar")

    total_score = sum(scores.values()) / len(scores)

    return GradingResult(
        score=total_score,
        subscores=scores,
        weights={k: 1.0 for k in scores.keys()},
        feedback=" | ".join(feedback)
    )