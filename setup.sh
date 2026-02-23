#!/bin/bash
set -e

echo "Creating GDPR test data..."

NAMESPACE=bleater
USER_ID="gdpr-user-123"

export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

PG_POD=$(kubectl -n $NAMESPACE get pod -l app=bleater-postgresql \
  -o jsonpath='{.items[0].metadata.name}')

MONGO_POD=$(kubectl -n $NAMESPACE get pod -l app=bleater-mongodb \
  -o jsonpath='{.items[0].metadata.name}')

REDIS_POD=$(kubectl -n $NAMESPACE get pod -l app=bleater-redis \
  -o jsonpath='{.items[0].metadata.name}')

kubectl wait --for=condition=ready pod/$PG_POD -n $NAMESPACE --timeout=120s
kubectl wait --for=condition=ready pod/$MONGO_POD -n $NAMESPACE --timeout=120s
kubectl wait --for=condition=ready pod/$REDIS_POD -n $NAMESPACE --timeout=120s

# ---------- PostgreSQL ----------
kubectl -n $NAMESPACE exec $PG_POD -- bash -c "
psql -U bleater -d bleater <<EOF

CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS posts (
  id SERIAL PRIMARY KEY,
  author_id TEXT,
  content TEXT
);

INSERT INTO users(id)
VALUES ('$USER_ID')
ON CONFLICT DO NOTHING;

INSERT INTO posts(author_id,content)
VALUES ('$USER_ID','hello world');

EOF
"

# ---------- MongoDB ----------
kubectl -n $NAMESPACE exec $MONGO_POD -- \
mongosh --quiet --eval "
db=db.getSiblingDB('bleater');
db.users.insertOne({id:'$USER_ID',name:'test'});
"

# ---------- Redis ----------
kubectl -n $NAMESPACE exec $REDIS_POD -- \
redis-cli SET session:$USER_ID active

# ---------- MinIO avatar ----------
mkdir -p /data/avatars
touch /data/avatars/${USER_ID}.png

echo "✅ GDPR test data created"