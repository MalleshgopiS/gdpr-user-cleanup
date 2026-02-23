FROM nebula-devops:1.0.0

WORKDIR /workspace

COPY setup.sh /workspace/setup.sh
COPY solution.sh /workspace/solution.sh
COPY task.yaml /workspace/task.yaml
COPY grader.py /tests/grader.py

RUN chmod +x /workspace/setup.sh /workspace/solution.sh

CMD ["python3", "/tests/grader.py"]