# ---------- MINIO ----------
mc alias set local http://minio:9000 minioadmin minioadmin

mc mb local/avatars || true

echo "avatar-data" > avatar.png
mc cp avatar.png local/avatars/user123.png