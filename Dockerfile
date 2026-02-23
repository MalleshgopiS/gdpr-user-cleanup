FROM nebula-devops:latest

WORKDIR /root

COPY setup.sh /root/setup.sh
COPY grader.py /root/grader.py

RUN chmod +x /root/setup.sh