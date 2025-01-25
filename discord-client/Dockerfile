FROM python:3.11-alpine

WORKDIR app/

COPY . .

RUN pip install -r requirements.txt --no-cache-dir
RUN pip install --upgrade discord.py aiohttp --no-cache-dir

CMD ["python", "main.py"]
