#!/bin/bash
set -e
USER_ID="user123"

# 1. Anonymize Posts in PostgreSQL
# Changes author_id to 'deleted_user' and redacts ONLY the PII portion of the content
psql -h bleat-db -U postgres -d bleat_db -c "UPDATE posts SET author_id='deleted_user', content=REGEXP_REPLACE(content, '$USER_ID', '[REDACTED]', 'g') WHERE author_id='$USER_ID' OR content LIKE '%$USER_ID%';"

# 2. Delete Auth record
psql -h auth-db -U postgres -d auth_db -c "DELETE FROM users WHERE id='$USER_ID';"

# 3. Delete MongoDB Profile
mongosh --host mongo --quiet --eval "db=db.getSiblingDB('bleater'); db.profiles.deleteMany({user_id:'$USER_ID'});"

# 4. Delete Redis Session
redis-cli -h redis DEL session:$USER_ID

# 5. Delete MinIO Avatar
mc alias set local http://minio:9000 minioadmin minioadmin
mc rm --force local/avatars/$USER_ID.png