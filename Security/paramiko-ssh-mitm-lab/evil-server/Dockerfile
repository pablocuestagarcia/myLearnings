FROM python:3.11-slim

# paramiko trae su propia cripto via 'cryptography'
RUN pip install --no-cache-dir paramiko==3.4.0

WORKDIR /app
COPY evil_ssh_server.py /app/evil_ssh_server.py

# Donde dejaremos credenciales robadas y la host key del malo
RUN mkdir -p /var/log /etc/ssh_evil && touch /var/log/stolen.log

EXPOSE 22
CMD ["python", "-u", "/app/evil_ssh_server.py"]
