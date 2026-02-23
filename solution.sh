#!/bin/bash
set -e

export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

NS="bleater"
USER_ID="user123"

echo "Running GDPR cleanup..."

kubectl exec deploy/auth-db -n $NS -- \
psql -U postgres -d auth_db \
-c "DELETE FROM users WHERE id='$USER_ID';"

kubectl exec deploy/bleat-db -n $NS -- \
psql -U postgres -d bleater_db \
-c "UPDATE posts
SET author_id='deleted_user',
    content='[redacted]'
WHERE author_id='$USER_ID';"

kubectl exec deploy/mongodb -n $NS -- \
mongosh --eval \
"db.getSiblingDB('bleater').profiles.deleteOne({user_id:'$USER_ID'})"

kubectl exec deploy/redis -n $NS -- \
redis-cli DEL session:$USER_ID || true

kubectl exec deploy/minio -n $NS -- \
rm -f /data/avatars/${USER_ID}.png || true

echo "GDPR cleanup completed."