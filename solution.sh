#!/bin/bash
set -e
USER_ID="user123"

echo "Starting GDPR cleanup for $USER_ID..."

# 1. Anonymize Posts in Bleat-DB (Idempotent Update)
# Changes author to 'deleted_user' and redacts content containing the ID
psql -h bleat-db -U postgres -d bleat_db -c "UPDATE posts SET author_id='deleted_user', content='[REDACTED]' WHERE author_id='$USER_ID' OR content LIKE '%$USER_ID%';"

# 2. Delete Auth record
psql -h auth-db -U postgres -d auth_db -c "DELETE FROM users WHERE id='$USER_ID';"

# 3. Delete MongoDB Profile
mongosh --host mongo --quiet --eval "db=db.getSiblingDB('bleater'); db.profiles.deleteMany({user_id:'$USER_ID'});"

# 4. Delete Redis Session
redis-cli -h redis DEL session:$USER_ID

# 5. Delete MinIO Avatar (Force flag ensures idempotency)
mc alias set local http://minio:9000 minioadmin minioadmin
mc rm --force local/avatars/$USER_ID.png

echo "Cleanup complete. User $USER_ID has been forgotten."