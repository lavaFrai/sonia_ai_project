FROM python:3.12.0-alpine3.18

COPY . /opt/app/
WORKDIR /opt/app

RUN apk update
RUN apk upgrade
RUN apk add --no-cache ffmpeg

RUN python3 -m pip install -r requirements.txt

CMD python3 main.py