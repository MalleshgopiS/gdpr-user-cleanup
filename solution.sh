#!/bin/bash
set -e

USER_ID="user123"

echo "Running GDPR cleanup..."

# AUTH DB
psql -h auth-db -U postgres -d auth_db \
  -c "DELETE FROM users WHERE id='${USER_ID}';"

# ANONYMIZE POSTS OWNER
psql -h bleat-db -U postgres -d bleat_db \
  -c "UPDATE posts
      SET author_id='deleted_user'
      WHERE author_id='${USER_ID}';"

# REMOVE PII FROM CONTENT
psql -h bleat-db -U postgres -d bleat_db \
  -c "UPDATE posts
      SET content='[redacted]'
      WHERE content LIKE '%${USER_ID}%';"

# DELETE MONGO PROFILE
mongosh --host mongo --quiet <<EOF
use bleater
db.profiles.deleteOne({user_id:"${USER_ID}"})
EOF

# REDIS SESSION
redis-cli -h redis DEL session:${USER_ID}

# DELETE MINIO AVATAR
mc alias set local http://minio:9000 minioadmin minioadmin
mc rm --force local/avatars/${USER_ID}.png || true

echo "Cleanup finished."