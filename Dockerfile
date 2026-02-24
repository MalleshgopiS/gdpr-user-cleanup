FROM us-central1-docker.pkg.dev/bespokelabs/nebula-devops-registry/nebula-devops:1.0.0

USER root

# Install database clients
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    curl \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/* # Install Mongo shell (mongosh)
RUN wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add - && \
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" \
    > /etc/apt/sources.list.d/mongodb-org.list && \
    apt-get update && apt-get install -y mongodb-mongosh 

# Install MinIO client (mc)
RUN curl -fsSL https://dl.min.io/client/mc/release/linux-amd64/mc \
    -o /usr/local/bin/mc && chmod +x /usr/local/bin/mc 

WORKDIR /workspace
COPY setup.sh /tests/setup.sh
COPY grader.py /tests/grader.py
COPY solution.sh /workspace/solution.sh
COPY task.yaml /workspace/task.yaml

RUN chmod +x /tests/setup.sh /workspace/solution.sh
CMD ["python3", "/tests/grader.py"]