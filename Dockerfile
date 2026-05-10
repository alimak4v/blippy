FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    g++ \
    build-essential \
    python3-dev \
    libdbus-1-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pybind11

COPY . .

RUN mkdir -p storage

RUN g++ -O3 -Wall -shared -std=c++11 -fPIC \
    $(python3 -m pybind11 --includes) \
    secure_codex.cpp \
    -o secure_codex$(python3-config --extension-suffix)

CMD ["python", "main.py"]
