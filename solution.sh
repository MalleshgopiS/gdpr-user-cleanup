#!/bin/bash
set -e

USER_ID="user123"

echo "Running GDPR cleanup..."

# Delete auth record
psql -h auth-db -U postgres -d auth_db \
  -c "DELETE FROM users WHERE id='${USER_ID}';"

# Anonymize posts
psql -h bleat-db -U postgres -d bleat_db \
  -c "
  UPDATE posts
  SET author_id='deleted_user',
      content=''
  WHERE author_id='${USER_ID}'
     OR content LIKE '%${USER_ID}%';
  "

# Remove Mongo profile
mongosh --host mongo bleater --eval \
"db.profiles.deleteOne({user_id:'${USER_ID}'})"

# Remove Redis session
redis-cli -h redis DEL session:${USER_ID}

# Remove avatar
mc alias set minio http://minio:9000 minioadmin minioadmin || true
mc rm --force minio/avatars/${USER_ID}.png || true

echo "GDPR cleanup finished."