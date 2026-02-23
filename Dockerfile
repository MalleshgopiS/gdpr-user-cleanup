FROM nebula-devops:1.0.0

RUN pip3 install \
    psycopg2-binary==2.9.9 \
    pymongo==4.6.1 \
    redis==5.0.1 \
    requests==2.31.0

# Agent workspace
WORKDIR /workspace
COPY setup.sh .

# Hidden grader (agent cannot see)
WORKDIR /tests
COPY grader.py .

CMD ["python3", "/tests/grader.py"]