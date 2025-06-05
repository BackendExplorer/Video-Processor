FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app/

RUN pip install --no-cache-dir \
      ffmpeg-python \
      pycryptodome

EXPOSE 9001
CMD ["python", "server.py"]
