#!/bin/bash
set -e

# ---------------------- [DONOT CHANGE ANYTHING BELOW] ---------------------------------- #
echo "Ensuring supervisord is running..."
/usr/bin/supervisord -c /etc/supervisor/supervisord.conf 2>/dev/null || true
sleep 5

export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

echo "Waiting for k3s to be ready..."
MAX_WAIT=180
ELAPSED=0
until kubectl get nodes &>/dev/null; do
    if [ $ELAPSED -ge $MAX_WAIT ]; then
        echo "Error: k3s is not ready after ${MAX_WAIT} seconds"
        exit 1
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done
echo "k3s is ready!"
# ---------------------- [DONOT CHANGE ANYTHING ABOVE] ---------------------------------- #

USER_ID="user123"
echo "Seeding GDPR violation data for $USER_ID..."

# Seed Auth DB
psql -h auth-db -U postgres -d auth_db -c "INSERT INTO users(id, email) VALUES('$USER_ID', 'user@test.com') ON CONFLICT (id) DO NOTHING;"

# Seed Posts
psql -h bleat-db -U postgres -d bleat_db -c "INSERT INTO posts(author_id, content) VALUES('$USER_ID', 'Hello from $USER_ID');"
psql -h bleat-db -U postgres -d bleat_db -c "INSERT INTO posts(author_id, content) VALUES('other_user', 'Hey $USER_ID, how are you?');"

# Seed Profile
mongosh --host mongo --quiet --eval "db=db.getSiblingDB('bleater'); db.profiles.updateOne({user_id:'$USER_ID'}, {\$set: {user_id:'$USER_ID', bio:'PII Data'}}, {upsert:true});"

# Seed Session
redis-cli -h redis SET session:$USER_ID "active"

# Seed Avatar
mc alias set local http://minio:9000 minioadmin minioadmin
mc mb local/avatars || true
echo "avatar-content" > /tmp/avatar.png
mc cp /tmp/avatar.png local/avatars/$USER_ID.png

echo "Seed complete."