FROM python:3.11-alpine

WORKDIR api/

COPY . .

RUN pip install -r requirements.txt --no-cache-dir

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "9462"]
