import json
import os

import asyncio

import config

from flask import Flask, make_response, jsonify, request

from generator import Generator

app = Flask(__name__)
if os.environ.get('AUTH_TYPE') == "iam":
    with open(os.environ.get('TOKEN')) as token_file:
        token = token_file.read().strip()
else:
    with open(os.environ.get('API_KEY')) as token_file:
        token = token_file.read().strip()
with open(os.environ.get('MODEL_URI')) as model_uri_file:
    model_uri = model_uri_file.read().strip()

gen = Generator(token)
gen.TEMPLATE["modelUri"] = model_uri


@app.route('/generator/api/v1/catastrophe', methods=['POST'])
async def generate_catastrophe():
    cat = {}
    limit = 4
    while cat == {}:
        try:
            cat = await gen.generate_catastrophe()
        except (KeyError, json.decoder.JSONDecodeError):
            limit -= 1
            await asyncio.sleep(1)
            cat = {}
        if limit == 0:
            return make_response(jsonify({"status": False}), 502)
    return make_response(jsonify(cat), 201)


@app.route('/generator/api/v1/bunker', methods=['POST'])
async def generate_bunker():
    bunker = {}
    limit = 4
    while bunker == {}:
        try:
            bunker = await gen.generate_bunker()
        except (KeyError, json.decoder.JSONDecodeError):
            limit -= 1
            await asyncio.sleep(1)
            bunker = {}
        if limit == 0:
            return make_response(jsonify({"status": False}), 502)
    return make_response(jsonify(bunker), 201)


@app.route('/generator/api/v1/player/<game_code>', methods=['POST'])
async def generate_player(game_code):
    user_data = {}
    limit = 4
    while user_data == {} or limit == 0:
        try:
            user_data = await gen.generate_player(game_code)
            if list(user_data.keys()) != [
                'gender', 'luggage', 'fact1', 'fact2', 'age',
                'action_card', 'phobia', 'health', 'profession', 'hobby'
            ]:
                user_data = {}
                limit -= 1
                await asyncio.sleep(1)
        except (KeyError, json.decoder.JSONDecodeError, IndexError) as e:
            limit -= 1
            await asyncio.sleep(1)
            user_data = {}
        if limit == 0:
            return make_response(jsonify({"status": False}), 502)
    gen.games[game_code].add_user_data(user_data)
    return make_response(jsonify(user_data), 201)


@app.route('/generator/api/v1/bunker-result', methods=['POST'])
async def generate_bunker_result():
    result = {}
    limit = 4
    while result == {}:
        try:
            result = await gen.generate_bunker_result(request.json)
            if list(result.keys()) != ["result"]:
                result = {}
                limit -= 1
                await asyncio.sleep(1)
        except (KeyError, json.decoder.JSONDecodeError):
            result = {}
            limit -= 1
            await asyncio.sleep(1)
    if limit == 0:
        return make_response(jsonify({"status": False}), 502)
    return make_response(jsonify(result), 201)


@app.route('/generator/api/v1/get-active-card/<card>', methods=['GET'])
async def get_active_card(card):
    for i in config.active_cards:
        if i["card"] == card:
            return make_response(jsonify(i), 201)
    return make_response({"card": "", "id": -1}, 404)


@app.route('/generator/api/v1/result', methods=['POST'])
async def generate_result():
    result = {}
    limit = 4
    while result == {}:
        try:
            result = await gen.generate_result(request.json)
            if list(result.keys()) != ["result"]:
                result = {}
                limit -= 1
        except (KeyError, json.decoder.JSONDecodeError):
            limit -= 1
            result = {}
            await asyncio.sleep(1)
        if limit == 0:
            return make_response(jsonify({"status": False}), 502)
    return make_response(jsonify(result), 201)
