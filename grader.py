import subprocess
import time

USER_ID="user123"

def run(cmd):
    return subprocess.run(cmd,shell=True,capture_output=True,text=True)

def sql_count(host,db,q):
    r=run(f'psql -h {host} -U postgres -d {db} -t -c "{q}"')
    return int(r.stdout.strip())

def auth_deleted():
    return sql_count("auth-db","auth_db",
        f"SELECT COUNT(*) FROM users WHERE id='{USER_ID}';")==0

def posts_clean():
    total=sql_count("bleat-db","bleat_db","SELECT COUNT(*) FROM posts;")
    owned=sql_count("bleat-db","bleat_db",
        f"SELECT COUNT(*) FROM posts WHERE author_id='{USER_ID}';")
    pii=sql_count("bleat-db","bleat_db",
        f"SELECT COUNT(*) FROM posts WHERE content LIKE '%{USER_ID}%';")
    return total>0 and owned==0 and pii==0

def mongo_deleted():
    r=run(
      f"mongosh --host mongo --quiet --eval "
      f"\"db=db.getSiblingDB('bleater');print(db.profiles.countDocuments({{user_id:'{USER_ID}'}}));\""
    )
    return r.stdout.strip()=="0"

def redis_deleted():
    r=run(f"redis-cli -h redis EXISTS session:{USER_ID}")
    return r.stdout.strip()=="0"

def avatar_deleted():
    r=run(
        f"mc alias set local http://minio:9000 minioadmin minioadmin && "
        f"mc stat local/avatars/{USER_ID}.png"
    )
    return r.returncode!=0

def idempotent():
    return subprocess.run(["bash","/workspace/solution.sh"]).returncode==0

def main():
    subprocess.run(["bash","/tests/setup.sh"],check=True)

    # wait until postgres ready (no magic sleep)
    for _ in range(20):
        if run("pg_isready -h auth-db").returncode==0:
            break
        time.sleep(1)

    subprocess.run(["bash","/workspace/solution.sh"],check=True)

    checks=[
        auth_deleted(),
        posts_clean(),
        mongo_deleted(),
        redis_deleted(),
        avatar_deleted(),
        idempotent()
    ]

    if all(checks):
        print("SUCCESS")
        exit(0)
    else:
        print("FAIL")
        exit(1)

if __name__=="__main__":
    main()