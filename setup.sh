#!/bin/bash
set -e

/usr/bin/supervisord -c /etc/supervisor/supervisord.conf 2>/dev/null || true
sleep 5

export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

until kubectl get nodes &>/dev/null; do
  sleep 2
done

NS="bleater"
USER_ID="user123"

echo "Creating GDPR test data..."

kubectl exec deploy/auth-db -n $NS -- \
psql -U postgres -d auth_db \
-c "INSERT INTO users(id,email)
VALUES('$USER_ID','user@test.com')
ON CONFLICT DO NOTHING;"

kubectl exec deploy/bleat-db -n $NS -- \
psql -U postgres -d bleater_db \
-c "INSERT INTO posts(author_id,content)
VALUES('$USER_ID','hello world');"

kubectl exec deploy/mongodb -n $NS -- \
mongosh --eval \
"db.getSiblingDB('bleater').profiles.updateOne(
 {user_id:'$USER_ID'},
 {\$set:{name:'Test User'}},
 {upsert:true})"

kubectl exec deploy/redis -n $NS -- \
redis-cli SET session:$USER_ID active

kubectl exec deploy/minio -n $NS -- \
sh -c "mkdir -p /data/avatars && touch /data/avatars/${USER_ID}.png"

echo "Setup complete."