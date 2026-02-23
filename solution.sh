#!/bin/bash
set -e

export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

NAMESPACE=bleater
USER_ID="gdpr-user-123"

PG_POD=$(kubectl -n $NAMESPACE get pod -l app=bleater-postgresql \
  -o jsonpath='{.items[0].metadata.name}')

MONGO_POD=$(kubectl -n $NAMESPACE get pod -l app=bleater-mongodb \
  -o jsonpath='{.items[0].metadata.name}')

REDIS_POD=$(kubectl -n $NAMESPACE get pod -l app=bleater-redis \
  -o jsonpath='{.items[0].metadata.name}')

echo "Running GDPR cleanup..."

# ---------- PostgreSQL ----------
kubectl -n $NAMESPACE exec $PG_POD -- bash -c "
psql -U bleater -d bleater <<EOF

DELETE FROM users WHERE id='$USER_ID';

UPDATE posts
SET author_id='deleted_user',
    content=''
WHERE author_id='$USER_ID';

EOF
"

# ---------- MongoDB ----------
kubectl -n $NAMESPACE exec $MONGO_POD -- \
mongosh --quiet --eval "
db=db.getSiblingDB('bleater');
db.users.deleteOne({id:'$USER_ID'});
"

# ---------- Redis ----------
kubectl -n $NAMESPACE exec $REDIS_POD -- \
redis-cli DEL session:$USER_ID || true

# ---------- MinIO avatar ----------
rm -f /data/avatars/${USER_ID}.png || true

echo "✅ GDPR cleanup completed"