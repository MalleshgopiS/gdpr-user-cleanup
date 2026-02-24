#!/bin/bash
set -e
USER_ID="user123"

echo "Seeding GDPR violation data for $USER_ID..."

# Seed Auth DB
psql -h auth-db -U postgres -d auth_db -c "INSERT INTO users(id, email) VALUES('$USER_ID', 'user@test.com') ON CONFLICT (id) DO NOTHING;"

# Seed Posts (One by the user, one by someone else mentioning the user)
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