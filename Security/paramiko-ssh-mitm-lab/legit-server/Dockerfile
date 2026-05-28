FROM debian:12-slim

# Reintentos + timeout largo en apt: el CDN de deb.debian.org (Fastly) corta
# a veces conexiones a la mitad. Asi el build aguanta blips de red en lugar
# de fallar entero.
RUN echo 'Acquire::Retries "10";' > /etc/apt/apt.conf.d/80-retries \
 && echo 'Acquire::http::Timeout "60";' >> /etc/apt/apt.conf.d/80-retries \
 && echo 'Acquire::https::Timeout "60";' >> /etc/apt/apt.conf.d/80-retries

# OpenSSH server real
RUN apt-get update \
 && apt-get install -y --no-install-recommends openssh-server \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /var/run/sshd

# Usuario de la "VM legitima" (equivalente a la VM remota a la que se conecta
# el job Python por SFTP en produccion).
RUN useradd -m -s /bin/bash appuser \
 && echo 'appuser:s3cret-pharma-data' | chpasswd

# Fichero que el cliente va a leer por SFTP
RUN mkdir -p /data \
 && echo 'datos confidenciales del pharma pipeline' > /data/secret.txt \
 && chown -R appuser:appuser /data \
 && chmod 600 /data/secret.txt

# Generar host keys *nuevas* durante el build, distintas de las del atacante
RUN rm -f /etc/ssh/ssh_host_*_key* \
 && ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -N '' \
 && ssh-keygen -t rsa -b 2048 -f /etc/ssh/ssh_host_rsa_key -N ''

# Permitir auth por password (es lo que reproduce el patron real)
RUN sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config \
 && sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config \
 && sed -i 's/^#\?UsePAM.*/UsePAM yes/' /etc/ssh/sshd_config

EXPOSE 22
# -D = foreground, -e = log a stderr (lo veremos con docker logs)
CMD ["/usr/sbin/sshd", "-D", "-e"]
