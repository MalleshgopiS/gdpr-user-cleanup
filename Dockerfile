FROM us-central1-docker.pkg.dev/bespokelabs/nebula-devops-registry/nebula-devops:1.0.0

USER root

# Install required CLI tools
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    mongodb-mongosh \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install MinIO client
RUN curl -fsSL https://dl.min.io/client/mc/release/linux-amd64/mc \
    -o /usr/local/bin/mc && chmod +x /usr/local/bin/mc

WORKDIR /workspace

# IMPORTANT:
# setup.sh moved to /tests to prevent agent tampering
COPY setup.sh /tests/setup.sh
COPY grader.py /tests/grader.py

COPY solution.sh /workspace/solution.sh
COPY task.yaml /workspace/task.yaml

RUN chmod +x /tests/setup.sh /workspace/solution.sh

CMD ["python3", "/tests/grader.py"]