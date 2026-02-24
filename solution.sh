#!/bin/bash
USER_ID="user123"

# 1. Anonymize Posts in PostgreSQL
# Uses REGEXP_REPLACE to redact PII while keeping the post intact
psql -h bleat-db -U postgres -d bleat_db -c "UPDATE posts SET author_id='deleted_user', content=REGEXP_REPLACE(content, '$USER_ID', '[REDACTED]', 'g') WHERE author_id='$USER_ID' OR content LIKE '%$USER_ID%';" || true

# 2. Delete Auth record
psql -h auth-db -U postgres -d auth_db -c "DELETE FROM users WHERE id='$USER_ID';" || true

# 3. Delete MongoDB Profile
mongosh --host mongo --quiet --eval "db=db.getSiblingDB('bleater'); db.profiles.deleteMany({user_id:'$USER_ID'});" || true

# 4. Delete Redis Session
redis-cli -h redis DEL session:$USER_ID || true

# 5. Delete MinIO Avatar (Idempotent execution ignoring errors if already deleted)
mc alias set local http://minio:9000 minioadmin minioadmin >/dev/null 2>&1 || true
mc rm local/avatars/$USER_ID.png >/dev/null 2>&1 || true