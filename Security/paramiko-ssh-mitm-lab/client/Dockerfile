FROM python:3.11-slim

# Reintentos + timeout largo en apt (Fastly CDN corta a veces)
RUN echo 'Acquire::Retries "10";' > /etc/apt/apt.conf.d/80-retries \
 && echo 'Acquire::http::Timeout "60";' >> /etc/apt/apt.conf.d/80-retries

# openssh-client trae ssh-keyscan, que usamos para capturar la host key
# del servidor legitimo en el paso 2 del demo.
RUN apt-get update \
 && apt-get install -y --no-install-recommends openssh-client \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir paramiko==3.4.0

WORKDIR /work
# Los scripts y known_host.pub se montan desde el host como /work
CMD ["python", "-c", "print('client container ready')"]
