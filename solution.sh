#!/bin/bash
set -e

USER_ID="user123"

export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

echo "Running GDPR cleanup..."

# AUTH DB
psql -h auth-db -U postgres -d auth_db \
  -c "DELETE FROM users WHERE id='${USER_ID}';"

# POSTS (ANONYMIZE)
psql -h bleat-db -U postgres -d bleat_db \
  -c "UPDATE posts
      SET author_id='deleted_user',
          content='[redacted]'
      WHERE author_id='${USER_ID}';"

# MONGO
mongosh --quiet <<EOF
use bleater
db.profiles.deleteOne({user_id:"${USER_ID}"})
EOF

# REDIS
redis-cli -h redis DEL session:${USER_ID}

# MINIO
mc alias set local http://minio:9000 minioadmin minioadmin
mc rm --force local/avatars/${USER_ID}.png || true

echo "Cleanup finished."