FROM us-central1-docker.pkg.dev/bespokelabs/nebula-devops-registry/nebula-devops:1.0.0

USER root

RUN apt-get update && apt-get install -y \
    postgresql-client=14* \
    redis-tools=5* \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Mongo shell (stable package)
RUN wget -qO - https://pgp.mongodb.com/server-6.0.asc | apt-key add - && \
    echo "deb [ arch=amd64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" \
    > /etc/apt/sources.list.d/mongodb-org.list && \
    apt-get update && apt-get install -y mongodb-mongosh

# Pin MinIO client version
RUN curl -fsSL https://dl.min.io/client/mc/release/linux-amd64/archive/mc.RELEASE.2024-02-29T19-21-29Z \
    -o /usr/local/bin/mc && chmod +x /usr/local/bin/mc

WORKDIR /workspace

# Protect grader + setup
COPY setup.sh /tests/setup.sh
COPY grader.py /tests/grader.py

COPY solution.sh /workspace/solution.sh
COPY task.yaml /workspace/task.yaml

RUN chmod +x /tests/setup.sh /workspace/solution.sh

CMD ["python3", "/tests/grader.py"]