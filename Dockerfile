FROM nebula-devops:1.0.0

RUN pip3 install psycopg2-binary pymongo redis requests

ENV KUBECONFIG=/etc/rancher/k3s/k3s.yaml

WORKDIR /workspace

COPY setup.sh .
COPY grader.py .

RUN chmod +x setup.sh

CMD ["python3", "grader.py"]