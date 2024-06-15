FROM huecker.io/library/python:3.11

WORKDIR api/

COPY . .

RUN pip install -r requirements.txt

CMD ["flask", "run"]