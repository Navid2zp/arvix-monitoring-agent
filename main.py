import secrets
from configparser import ConfigParser
from functools import wraps

import requests
from flask import Flask, jsonify, request
from tractus import Tracer


def set_config(flask_app: Flask):
    config = ConfigParser()
    config.read('config.cfg')
    flask_app.config.update(
        SETUP_STATUS=config["STATE"].getboolean("SETUP_STATUS"),
        AGENT_NAME=config["STATE"].get("AGENT_NAME"),
        AGENT_ID=config["STATE"].get("AGENT_ID"),
        AGENT_SECRET=config["STATE"].get("AGENT_SECRET"),
    )


app = Flask(__name__)
set_config(app)


def authentication_required():
    def _authentication_required(f):
        @wraps(f)
        def __authentication_required(*args, **kwargs):
            # just do here everything what you need
            secret = request.headers.get("Secret")
            if not secret or secret != app.config.get("AGENT_SECRET"):
                return "Access denied", 403
            result = f(*args, **kwargs)
            return result

        return __authentication_required

    return _authentication_required


@app.route('/setup', methods=['POST'])
def setup():
    if app.config.get("SETUP_STATUS"):
        return jsonify({"status": "error", "error": "SETUP_ALREADY_DONE"}), 400

    config = ConfigParser()
    config.read('config.cfg')

    secret = secrets.token_hex(64)
    name = request.json["name"]
    agent_id = request.json["id"]

    config["STATE"]["AGENT_NAME"] = str(name)
    config["STATE"]["AGENT_ID"] = str(agent_id)
    config["STATE"]["AGENT_SECRET"] = secret
    config["STATE"]["SETUP_STATUS"] = "True"
    with open('config.cfg', 'w') as configfile:
        config.write(configfile)
    set_config(app)

    return jsonify({
        "status": "ok",
        "data": {
            "secret": secret,
            "name": name,
            "id": agent_id,
            "location": requests.get("https://ipapi.co/json/").json()["country"]
        }
    })


@app.route('/trace')
@authentication_required()
def index():
    url = request.args.get("url", "")
    tracer = Tracer(url).trace()
    return jsonify(tracer.as_dict())


if __name__ == '__main__':
    app.run(debug=True)
