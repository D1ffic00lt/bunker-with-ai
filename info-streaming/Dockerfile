FROM python:3.11-alpine

WORKDIR live-video/

COPY . .

RUN pip install -r requirements.txt --no-cache-dir

CMD ["flask", "run"]