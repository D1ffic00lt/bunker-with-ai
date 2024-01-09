import json
import os

from flask import Flask, make_response, jsonify, request

from generator import Generator

app = Flask(__name__)
with open(os.environ.get('TOKEN')) as token_file:
    token = token_file.read()
with open(os.environ.get('MODEL_URI')) as model_uri_file:
    model_uri = model_uri_file.read()

gen = Generator(token)
gen.TEMPLATE["modelUri"] = model_uri


@app.route('/generator/api/v1/catastrophe', methods=['POST'])
async def generate_catastrophe():
    cat = {}
    while cat == {}:
        try:
            cat = await gen.generate_catastrophe()
        except (KeyError, json.decoder.JSONDecodeError):
            cat = {}
    return make_response(jsonify(cat), 201)


@app.route('/generator/api/v1/bunker', methods=['POST'])
async def generate_bunker():
    bunker = {}
    while bunker == {}:
        try:
            bunker = await gen.generate_bunker()
        except (KeyError, json.decoder.JSONDecodeError):
            bunker = {}
    return make_response(jsonify(bunker), 201)


@app.route('/generator/api/v1/player/<game_code>', methods=['POST'])
async def generate_player(game_code):
    user_data = {}
    while user_data == {}:
        try:
            user_data = await gen.generate_player(game_code)
            if list(user_data.keys()) != [
                'gender', 'health', 'profession', 'hobby', 'luggage', 'fact1',
                'fact2', 'age', 'action_card', 'phobia'
            ]:
                user_data = {}
        except (KeyError, json.decoder.JSONDecodeError):
            user_data = {}
    return make_response(jsonify(user_data), 201)


@app.route('/generator/api/v1/bunker-result', methods=['POST'])
async def generate_bunker_result():
    result = {}
    while result == {}:
        try:
            result = await gen.generate_bunker_result(request.json)
            if list(result.keys()) != ["result"]:
                result = {}
        except (KeyError, json.decoder.JSONDecodeError):
            result = {}
    return make_response(jsonify(result), 201)


@app.route('/generator/api/v1/result', methods=['POST'])
async def generate_result():
    result = {}
    while result == {}:
        try:
            result = await gen.generate_result(request.json)
            if list(result.keys()) != ["result"]:
                result = {}
        except (KeyError, json.decoder.JSONDecodeError):
            result = {}
    return make_response(jsonify(result), 201)
