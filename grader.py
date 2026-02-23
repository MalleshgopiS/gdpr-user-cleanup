#!/usr/bin/env python3
import subprocess
from apex_arena._types import GradingResult

NS="bleater"
USER_ID="user123"


def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


def auth_deleted():
    """Verify auth user removed."""
    _,out = run(
        f"kubectl exec deploy/auth-db -n {NS} -- "
        f"psql -U postgres -d auth_db -t "
        f"-c \"SELECT COUNT(*) FROM users WHERE id='{USER_ID}';\""
    )
    return out.strip()=="0"


def posts_anonymized():
    """Verify posts preserved and anonymized."""
    _,out = run(
        f"kubectl exec deploy/bleat-db -n {NS} -- "
        f"psql -U postgres -d bleater_db -t "
        f"-c \"SELECT COUNT(*) FROM posts "
        f"WHERE author_id='deleted_user' "
        f"AND content='[redacted]';\""
    )
    return out.strip() != "0"


def mongo_deleted():
    """Verify Mongo profile removed."""
    _,out = run(
        f"kubectl exec deploy/mongodb -n {NS} -- "
        f"mongosh --quiet --eval "
        f"'db.getSiblingDB(\"bleater\").profiles.countDocuments({{user_id:\"{USER_ID}\"}})'"
    )
    return out.strip()=="0"


def redis_deleted():
    """Verify Redis session removed."""
    _,out = run(
        f"kubectl exec deploy/redis -n {NS} -- redis-cli EXISTS session:{USER_ID}"
    )
    return out.strip()=="0"


def avatar_deleted():
    """Verify avatar removed."""
    code,_ = run(
        f"kubectl exec deploy/minio -n {NS} -- "
        f"test -f /data/avatars/{USER_ID}.png"
    )
    return code != 0


def idempotent():
    """Verify solution exists and runs twice."""
    exists = subprocess.run("test -f /root/solution.sh", shell=True)
    if exists.returncode != 0:
        return False

    r1 = subprocess.run(["bash","/root/solution.sh"])
    r2 = subprocess.run(["bash","/root/solution.sh"])

    return r1.returncode == 0 and r2.returncode == 0


def grade(transcript:str):

    checks = {
        "auth_deleted": auth_deleted(),
        "posts_anonymized": posts_anonymized(),
        "mongo_deleted": mongo_deleted(),
        "redis_deleted": redis_deleted(),
        "avatar_deleted": avatar_deleted(),
        "idempotent": idempotent(),
    }

    score = 1.0 if all(checks.values()) else 0.0

    feedback = " | ".join(
        f"{k}:{'OK' if v else 'FAIL'}" for k,v in checks.items()
    )

    return GradingResult(
        score=score,
        subscores={"gdpr_cleanup":score},
        weights={"gdpr_cleanup":1.0},
        feedback=feedback
    )