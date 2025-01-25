FROM python:3.11-alpine

WORKDIR api/

COPY . .

RUN pip install -r requirements.txt --no-cache-dir

CMD ["flask", "run"]