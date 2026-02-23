#!/usr/bin/env bash
set -e

USER_ID="user123"

echo "Running GDPR cleanup..."

psql -h auth-db -U postgres -d auth_db \
  -c "DELETE FROM users WHERE id='$USER_ID';"

psql -h bleat-db -U postgres -d bleat_db \
  -c "UPDATE posts
      SET author_id='deleted_user',
          content=''
      WHERE author_id='$USER_ID'
         OR content LIKE '%$USER_ID%';"

mongosh --host mongo --quiet <<JS
db=db.getSiblingDB("bleater");
db.profiles.deleteMany({user_id:"$USER_ID"});
JS

redis-cli -h redis DEL session:$USER_ID || true

mc alias set local http://minio:9000 minioadmin minioadmin
mc rm --force local/avatars/$USER_ID.png || true

echo "Cleanup complete"