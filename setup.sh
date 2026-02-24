#!/bin/bash
set -e
USER_ID="user123"

echo "Seeding GDPR violation data for $USER_ID..."

# Seed Auth DB (PostgreSQL)
psql -h auth-db -U postgres -d auth_db -c "INSERT INTO users(id, email) VALUES('$USER_ID', 'user@test.com') ON CONFLICT (id) DO NOTHING;"

# Seed Posts (PostgreSQL) - Contains PII in content
psql -h bleat-db -U postgres -d bleat_db -c "INSERT INTO posts(author_id, content) VALUES('$USER_ID', 'This message belongs to $USER_ID');"

# Seed Profile (MongoDB)
mongosh --host mongo --quiet --eval "db=db.getSiblingDB('bleater'); db.profiles.updateOne({user_id:'$USER_ID'}, {\$set: {user_id:'$USER_ID', bio:'Secret Bio'}}, {upsert:true});"

# Seed Session (Redis)
redis-cli -h redis SET session:$USER_ID "active"

# Seed Avatar (MinIO)
mc alias set local http://minio:9000 minioadmin minioadmin
mc mb local/avatars || true
echo "avatar-content" > /tmp/avatar.png
mc cp /tmp/avatar.png local/avatars/$USER_ID.png

echo "Seed complete."