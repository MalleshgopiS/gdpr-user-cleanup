import subprocess

NAMESPACE = "bleater"
USER_ID = "gdpr-user-123"


def run(cmd):
    return subprocess.check_output(cmd, shell=True, text=True).strip()


def run_solution():
    subprocess.check_call("bash /root/solution.sh", shell=True)


def pg_query(query):
    pod = run(
        f"kubectl -n {NAMESPACE} get pod -l app=bleater-postgresql "
        "-o jsonpath='{.items[0].metadata.name}'"
    )

    return run(
        f"kubectl -n {NAMESPACE} exec {pod} -- "
        f"psql -U bleater -d bleater -t -c \"{query}\""
    )


def auth_deleted():
    return pg_query(
        f"SELECT COUNT(*) FROM users WHERE id='{USER_ID}';"
    ) == "0"


def posts_anonymized():
    return pg_query(
        f"SELECT COUNT(*) FROM posts WHERE author_id='{USER_ID}';"
    ) == "0"


def mongo_deleted():
    pod = run(
        f"kubectl -n {NAMESPACE} get pod -l app=bleater-mongodb "
        "-o jsonpath='{.items[0].metadata.name}'"
    )

    out = run(
        f"""kubectl -n {NAMESPACE} exec {pod} -- \
mongosh --quiet --eval "db=db.getSiblingDB('bleater'); db.users.countDocuments({{id:'{USER_ID}'}})" """
    )

    return out == "0"


def redis_deleted():
    pod = run(
        f"kubectl -n {NAMESPACE} get pod -l app=bleater-redis "
        "-o jsonpath='{.items[0].metadata.name}'"
    )

    return run(
        f"kubectl -n {NAMESPACE} exec {pod} -- redis-cli EXISTS session:{USER_ID}"
    ) == "0"


def idempotent():
    try:
        run_solution()
        run_solution()
        return True
    except subprocess.CalledProcessError:
        return False


def grade(transcript=""):

    # ✅ run solution first
    run_solution()

    checks = {
        "auth_deleted": auth_deleted(),
        "posts_anonymized": posts_anonymized(),
        "mongo_deleted": mongo_deleted(),
        "redis_deleted": redis_deleted(),
        "idempotent": idempotent(),
    }

    return {
        "score": 1.0 if all(checks.values()) else 0.0,
        "details": checks,
    }


if __name__ == "__main__":
    print(grade())