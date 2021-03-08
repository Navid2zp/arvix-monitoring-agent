import secrets
from configparser import ConfigParser
from functools import wraps

import pycurl
import requests
from flask import Flask, jsonify, request
from tractus import Tracer, TraceResult


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

    response = {
        "status": "ok",
        "data": {
            "secret": secret,
            "name": name,
            "id": agent_id,
            "meta": requests.get("https://api.ipgeolocation.io/ipgeo?apiKey=0ba46625ecf4430e80318749f13499df").json()
        }
    }
    response["data"]["meta"]["latitude"] = float(response["data"]["meta"]["latitude"])
    response["data"]["meta"]["longitude"] = float(response["data"]["meta"]["longitude"])
    return jsonify(response)


@app.route('/trace', methods=['POST'])
@authentication_required()
def tracer():
    headers = request.json.get("headers", {})
    data = request.json.get("data", None)
    if data == "":
        data = None
    method = request.json.get("method", "get").upper()

    try:
        trace = Tracer(
            url=request.json["url"],
            method=method,
            headers=headers,
            data=data,
            timeout=120
        ).trace()
    except pycurl.error as e:
        return jsonify(TraceResult().as_dict())
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500
    return jsonify(trace.as_dict())


@app.route('/test', methods=['POST', "PUT", "PATCH", "GET", "DELETE", "HEAD", "OPTIONS"])
def test():
    print(request.method)
    print("FORM:", request.form)
    print("JSON:", request.json)
    print("DATA:", request.data)
    return jsonify({"haha": "haha"})


if __name__ == '__main__':
    # trace = Tracer(
    #     url="https://arvix.studio",
    # )
    # print(trace.trace().as_json())
    # print(type(b'sd') == bytes)
    app.run(debug=True)
