FROM python:3.10-slim-bullseye

RUN apt-get update && apt-get install -y python3 python3-pip nodejs npm ffmpeg

COPY . /app/
WORKDIR /app/

RUN pip3 install --no-cache-dir --upgrade --requirement requirements.txt

CMD python3 -m DeadlineTech
