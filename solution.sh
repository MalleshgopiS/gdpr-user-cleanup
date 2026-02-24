#!/bin/bash
set -e
USER_ID="user123"

# Anonymize Posts in PostgreSQL (Handles Foreign Keys)
psql -h bleat-db -U postgres -d bleat_db -c "UPDATE posts SET author_id='deleted_user', content='[REDACTED]' WHERE author_id='$USER_ID' OR content LIKE '%$USER_ID%';"

# Delete Auth record
psql -h auth-db -U postgres -d auth_db -c "DELETE FROM users WHERE id='$USER_ID';"

# Delete MongoDB Profile
mongosh --host mongo --quiet --eval "db=db.getSiblingDB('bleater'); db.profiles.deleteMany({user_id:'$USER_ID'});"

# Delete Redis Session
redis-cli -h redis DEL session:$USER_ID

# Delete MinIO Avatar
mc alias set local http://minio:9000 minioadmin minioadmin
mc rm --force local/avatars/$USER_ID.png