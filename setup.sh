#!/usr/bin/env bash
set -e

USER_ID="user123"

echo "Seeding GDPR violation data..."

# Auth DB
psql -h auth-db -U postgres -d auth_db \
  -c "INSERT INTO users(id,email) VALUES('$USER_ID','user@test.com')
      ON CONFLICT DO NOTHING;"

# Bleat DB
psql -h bleat-db -U postgres -d bleat_db \
  -c "INSERT INTO posts(author_id,content)
      VALUES('$USER_ID','hello from $USER_ID');"

# MongoDB
mongosh --host mongo --quiet --eval "
db = db.getSiblingDB('bleater');
db.profiles.insertOne({user_id:'$USER_ID',name:'Test'});
"

# Redis
redis-cli -h redis SET session:$USER_ID active

# MinIO
mc alias set local http://minio:9000 minioadmin minioadmin
mc mb local/avatars || true
echo avatar > /tmp/avatar.png
mc cp /tmp/avatar.png local/avatars/$USER_ID.png || true

echo "Seed complete"