FROM python:3.11

WORKDIR app/

COPY . .

RUN pip install -r requirements.txt
RUN pip install --upgrade discord.py aiohttp

CMD ["python", "main.py"]
