FROM python:3.11

WORKDIR api/

COPY . .

RUN pip install -r requirements.txt

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "9462"]
