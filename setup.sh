#!/bin/bash
set -e
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
USER_ID="user123"

echo "Seeding GDPR violation data for $USER_ID..."

# Seed Auth DB (PostgreSQL)
psql -h auth-db -U postgres -d auth_db -c "INSERT INTO users(id, email) VALUES('$USER_ID', 'user@test.com') ON CONFLICT DO NOTHING;"

# Seed Posts (PostgreSQL) - Contains PII
psql -h bleat-db -U postgres -d bleat_db -c "INSERT INTO posts(author_id, content) VALUES('$USER_ID', 'Hello, this is $USER_ID message');"

# Seed Profile (MongoDB)
mongosh --host mongo --quiet --eval "db=db.getSiblingDB('bleater'); db.profiles.insertOne({user_id:'$USER_ID'});"

# Seed Session (Redis)
redis-cli -h redis SET session:$USER_ID "active"

# Seed Avatar (MinIO)
mc alias set local http://minio:9000 minioadmin minioadmin
mc mb local/avatars || true
echo "avatar-content" > /tmp/avatar.png
mc cp /tmp/avatar.png local/avatars/$USER_ID.png

echo "Seed complete."