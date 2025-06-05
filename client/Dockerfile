FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app/

RUN pip install --no-cache-dir \
      streamlit \
      ffmpeg-python \
      pycryptodome

EXPOSE 8501
CMD ["streamlit", "run", "gui.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
