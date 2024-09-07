<h1 align="center">The Bunker with AI</h1>
<p align="center"><strong>Bunker</strong> is a discussion game about surviving in the apocalypse. A global catastrophic is coming to Earth. You are lucky to be near the entrance to the bunker. You can try to survive the most dangerous scenario, but not everyone will enter there. You will need to make a choice. Who will enter and who will be outside? </p>

## About the bot
The Bunker Bot is a program for generating scenarios for playing bunker using AI. Every game has a global catastrophic scenario, a bunker description and a danger in the bunker that players will need to eliminate. 
### Player generation using AI
Each player has generated attributes:
- `Age` 
	
	For the balanced game, age generation is based on the exponential _function_.
	The _function_ is designed to generate ages mainly up to 20 years old, but less often it can output values higher, up to about 90 years old.

$$
get\\_age(x)= [\frac{e^{3log_2(x+1)}+ 0.9}{e^{-1.2x}}+17], 1\ge x\ge 0 , x \in \mathbb{R} 
$$
	
- `Gender`
	
	Gender generation does not need more flexible settings, so simple generation is implemented through the random library. There are _3_ genders in the game except for men and women. The rarest of them, a **vampire**, cannot have children’s, but they are immortal. **Androids** can solve a lot of problems in the bunker, but they also can’t have a children. **Humanoid-aliens** are a mysterious race, who knows if they are friends or enemies...
- `Profession`
	It is generated using AI. The most important attribute of your life.
- `Health`
	It is generated using AI. You can have any health problems, but you can also be completely healthy. Along with this characteristic comes the degree of the disease (%) – how much the disease progresses.
- `Hobby`
	It is generated using AI. Just a funny hobbies.
- `Luggage`
	It is generated using AI. Random things on your person. 
- `Phobia` 
	[Here](generator/config.py) you can find the full list with all kinds of phobias.  
- `First fact`
	It is generated using AI. Just a random fact about the player. 
- `Second fact`
	It is generated using AI. Just a random fact about the player. 
- `Active card`
	Active cards allow you to turn the game in your favor, here is a list of possible cards:
	- Exchange cards with a player of your choice
	- Exchanging cards with a random player
	- Shuffling the cards
	- Health Treatment
	- Changing the number of places in the bunker
	- Opening objects near the bunker
	- Limitation of player actions
## Installation and deployment

### 1. Docker installation 
The Bunker bot is based on the architecture of microservices, it uses [Docker](https://docker.com/) and [Docker Compose](https://docs.docker.com/compose/) for a correct and stable operation. 

There are eighth microservices in the project: 
- `bot` – Discord client. 
- `api` – API for connection to the database. 
- `main-generator` – the main Yandex Cloud AI scenarios generator.
- `reserve-generator` – the reserve Yandex Cloud AI scenarios generator.
- `generator` – Nginx load balancer.
- `info-streaming` – container for streaming frames. 
- `frame-generator` – user frame generator. 
- `redis` – in-memory database for fast frame acquisition.

You can install Docker and Docker Compose [here](https://docs.docker.com/engine/install/). 
### 2. Installation for server usage 
To install the bot, you can use an archive on the GitHub [realizes](https://github.com/D1ffic00lt/the-bunker-bot/releases) or git script
```bash
git clone https://github.com/d1ffic00lt/bunker-with-ai/
```

If you want to use program **locally**, you can change the ports in `docker-compose.yml`, `info-streaming`:

| Line | From                 | To                            |
| ---- | -------------------- | ----------------------------- |
| 84   | `FLASK_RUN_PORT: 80` | `FLASK_RUN_PORT: <your_port>` |
| 88   | `- "80:80"`          | `- "<your_port>:<your_port>"` |

As a example, you can use `<your_port>` as `3821`, for this, the container should look like that: 
```yml
info-streaming:  
  build: info-streaming/  
  restart: always  
  environment:  
    PYTHONDONTWRITEBYTECODE: 1  
    PYTHONUNBUFFERED: 1  
    FLASK_RUN_PORT: 3821 <-- there is new port here
    FLASK_RUN_HOST: 0.0.0.0  
    FLASK_APP: app.py  
  ports:
    - "3821:3821" <-- there are new ports here
  depends_on:  
    - api  
    - frame-generator  
    - redis
```
### 3. Requirements
The Bunker bot uses tokens to log in to [Discord](http://discord.com/developers/applications) and [Yandex Cloud](http://console.yandex.cloud/). So, you must create a directory with tokens for the correct use of the bot and the model.
```
.
├── README.md
├── api
├── directory-structure.md
├── discord-client
├── docker-compose.yml
├── frame-generator
├── generator
├── info-streaming
├── logs.bat
├── nginx
├── restart.bat
└── secrets
    ├── discord_token.txt
    ├── gpt-main
    │   ├── api_key.txt
    │   ├── model_uri.txt
    │   └── token.txt
    └── gpt-reserve
        ├── api_key.txt
        ├── model_uri.txt
        └── token.txt
```
- `discord_token.txt` 
	A _token_ for your own discord bot, you can get it on the [Discord Developer Portal](https://discord.com/developers/applications). Don't forget to enable `applications.commands` in the scopes of the bot. 
- `gpt-main`
	- `api_key.txt`

		The _api_key.txt_ is a secret key used for simplified authorization in the Yandex Cloud API. API keys are only used for [service account](https://yandex.cloud/en/docs/iam/concepts/users/service-accounts) authorization. [Here](https://yandex.cloud/en/docs/iam/concepts/authorization/api-key) is a [guide](https://yandex.cloud/en/docs/iam/concepts/authorization/api-key) on how can you get it for your account. 
	
	- `model_uri.txt`
	
		To [access](https://yandex.cloud/en/docs/foundation-models/operations/yandexgpt/create-prompt) your model via the API, under `modelUri`, specify its [URI](https://en.wikipedia.org/wiki/URI) which contains the [folder ID](https://yandex.cloud/en/docs/resource-manager/operations/folder/get-id).
		
	- `token.txt`
	
		In Yandex Cloud, an OAuth token is used to authenticate users with a Yandex account: the user exchanges an OAuth token for an [Identity and Access Management token](https://yandex.cloud/en/docs/iam/concepts/authorization/iam-token). [Here](https://yandex.cloud/en/docs/iam/concepts/authorization/oauth-token) is a [guide](https://yandex.cloud/en/docs/iam/concepts/authorization/oauth-token) on how can you get it for your account.
		 
- `gpt-reserve`
	- `api_key.txt`
	- `model_uri.txt`
	- `token.txt`

For the `gpt-reserve`, it is similar to the `gpt-main`. If you don't want to use `gpt-reserve`, you should copy the tokens and the model URI from  `gpt-main`.

You can use `token.txt` instead of `api_key.txt`, just turn it on in the `docker-compose.yml` in parameter`AUTH_TYPE`, it can be `api_key` for authorization via the API key or `iam` for authorization based on the IAM token. So, if you use `api_key.txt` instead of `token.txt`, `token.txt` can be empty, and vice versa.

### 4. Running
To launch the bot for the first time, you must launch Docker, log in to the console **in the bot directory** and send `docker-compose up`, then Docker will install all dependencies and start all services automatically.  

If you want to update the bot to a new version, you must send the `docker-compose build` to the console, after which you can start it again. 
