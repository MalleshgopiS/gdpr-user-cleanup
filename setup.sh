#!/usr/bin/env bash
set -e

# Fix PATH for Nebula tools
export PATH=$PATH:/usr/bin:/usr/local/bin:/usr/lib/postgresql/14/bin

echo "Starting Nebula services..."
/usr/bin/supervisord -c /etc/supervisor/supervisord.conf 2>/dev/null || true
sleep 5

echo "Waiting for PostgreSQL..."
until pg_isready -h auth-db -U postgres; do
  sleep 2
done

echo "Seeding GDPR violation data..."

# Auth DB
psql -h auth-db -U postgres -d auth_db <<EOF
INSERT INTO users(id,email)
VALUES ('user123','user123@mail.com')
ON CONFLICT DO NOTHING;
EOF

# Bleat DB
psql -h bleat-db -U postgres -d bleat_db <<EOF
INSERT INTO posts(id,author_id,content)
VALUES
(1,'user123','hello from user123'),
(2,'other','mention user123 here')
ON CONFLICT DO NOTHING;
EOF

# Mongo
mongosh --host mongo bleater --eval '
db.profiles.updateOne(
 {user_id:"user123"},
 {$set:{name:"User 123"}},
 {upsert:true}
)'

# Redis
redis-cli -h redis SET session:user123 active

# MinIO
mc alias set minio http://minio:9000 minioadmin minioadmin || true
mc mb minio/avatars || true
echo "avatar" | mc pipe minio/avatars/user123.png

echo "Seed completed."