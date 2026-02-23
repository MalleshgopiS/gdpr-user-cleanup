#!/bin/bash
set -e

USER_ID="user123"

echo "Seeding GDPR violation data..."

# AUTH DB
psql -U postgres -d auth_db <<EOF
CREATE TABLE IF NOT EXISTS users(
 id TEXT PRIMARY KEY,
 email TEXT
);

INSERT INTO users VALUES('$USER_ID','user@test.com')
ON CONFLICT DO NOTHING;
EOF

# POSTS DB
psql -U postgres -d bleat_db <<EOF
CREATE TABLE IF NOT EXISTS posts(
 id SERIAL PRIMARY KEY,
 author_id TEXT,
 content TEXT
);

INSERT INTO posts(author_id,content)
VALUES('$USER_ID','Hello from user123')
ON CONFLICT DO NOTHING;
EOF

# MONGO
mongosh --quiet --host mongo <<EOF
use bleater
db.profiles.updateOne(
 {user_id:"$USER_ID"},
 {\$set:{name:"Test User"}},
 {upsert:true}
)
EOF

# REDIS
redis-cli -h redis SET session:$USER_ID active

# MINIO
mc alias set local http://minio:9000 minioadmin minioadmin
mc mb local/avatars || true

echo "avatar" > avatar.png
mc cp avatar.png local/avatars/$USER_ID.png

echo "Setup complete."