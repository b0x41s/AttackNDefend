FROM python:3.9-slim

WORKDIR /app
COPY app.py requirements.txt ./
COPY templates/ ./templates/
COPY start.sh /start.sh
RUN pip install -r requirements.txt && \
    apt-get update && apt-get install -y openssh-server sqlite3 && \
    mkdir /var/run/sshd && \
    echo 'root:secret' | chpasswd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    chmod +x /start.sh

EXPOSE 5001 22
CMD ["/start.sh"]