#!/bin/bash
set -e
USER_ID="user123"

echo "Seeding GDPR violation data for $USER_ID..."

# 1. Seed Auth DB (PostgreSQL)
psql -h auth-db -U postgres -d auth_db -c "INSERT INTO users(id, email) VALUES('$USER_ID', 'user@test.com') ON CONFLICT (id) DO NOTHING;"

# 2. Seed Posts (PostgreSQL)
psql -h bleat-db -U postgres -d bleat_db -c "INSERT INTO posts(author_id, content) VALUES('$USER_ID', 'Private message from $USER_ID');"

# 3. Seed Profile (MongoDB)
mongosh --host mongo --quiet --eval "db=db.getSiblingDB('bleater'); db.profiles.updateOne({user_id:'$USER_ID'}, {\$set: {user_id:'$USER_ID', bio:'My secret bio'}}, {upsert:true});"

# 4. Seed Session (Redis)
redis-cli -h redis SET session:$USER_ID "active_session_token_123"

# 5. Seed Avatar (MinIO)
mc alias set local http://minio:9000 minioadmin minioadmin
mc mb local/avatars || true
echo "binary-image-data" > /tmp/avatar.png
mc cp /tmp/avatar.png local/avatars/$USER_ID.png

echo "Seed complete. Environment is now non-compliant."