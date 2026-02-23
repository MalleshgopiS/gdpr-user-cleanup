import subprocess
import time

USER_ID = "user123"


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def sql_count(host, db, query):
    r = run(f'psql -h {host} -U postgres -d {db} -t -c "{query}"')
    try:
        return int(r.stdout.strip())
    except:
        return -1


def auth_deleted():
    return sql_count("auth-db", "auth_db",
                     f"SELECT COUNT(*) FROM users WHERE id='{USER_ID}';") == 0


def posts_clean():
    total = sql_count("bleat-db", "bleat_db", "SELECT COUNT(*) FROM posts;")
    owned = sql_count("bleat-db", "bleat_db",
                      f"SELECT COUNT(*) FROM posts WHERE author_id='{USER_ID}';")
    pii = sql_count("bleat-db", "bleat_db",
                    f"SELECT COUNT(*) FROM posts WHERE content LIKE '%{USER_ID}%';")

    return total > 0 and owned == 0 and pii == 0


def mongo_deleted():
    r = run(
        f"mongosh --host mongo --quiet --eval \"db=db.getSiblingDB('bleater');print(db.profiles.countDocuments({{user_id:'{USER_ID}'}}));\""
    )
    return "0" in r.stdout


def redis_deleted():
    r = run(f"redis-cli -h redis GET session:{USER_ID}")
    return "(nil)" in r.stdout


def avatar_deleted():
    r = run(
        f"mc alias set local http://minio:9000 minioadmin minioadmin && "
        f"mc stat local/avatars/{USER_ID}.png"
    )
    return r.returncode != 0


def idempotent():
    r = subprocess.run(["bash", "/workspace/solution.sh"])
    return r.returncode == 0


def main():
    print("Running setup...")
    subprocess.run(["bash", "/tests/setup.sh"], check=True)

    time.sleep(8)

    print("Running solution...")
    subprocess.run(["bash", "/workspace/solution.sh"], check=True)

    checks = [
        auth_deleted(),
        posts_clean(),
        mongo_deleted(),
        redis_deleted(),
        avatar_deleted(),
        idempotent(),
    ]

    if all(checks):
        print("SUCCESS")
        exit(0)
    else:
        print("FAIL")
        exit(1)


if __name__ == "__main__":
    main()