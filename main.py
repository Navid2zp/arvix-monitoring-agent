import os
import secrets
from configparser import ConfigParser
from typing import Optional

import pycurl
import requests
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from tractus import Tracer, TraceResult

# Config file path
CONFIG_PATH = "config/config.cfg"


def get_config() -> ConfigParser:
    """
    Parse the config file.
    :return: config
    """
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    return cfg


app = FastAPI(debug=os.environ.get("DEBUG", "false").lower() == "true")
config: ConfigParser = get_config()


class SetupData(BaseModel):
    name: str
    id: str


@app.post("/setup")
async def setup(setup_data: SetupData):
    """
    This method is used to setup the agent for the first time.
    A token will be generated and will be returned as response so trace request can be authenticated with it.
    You need to provide a name and an id for the agent.
    It requires an API key from ipgeolocation.io for geo location data.
    :param setup_data: name and the id of the agent
    :return: Response containing authentication token and geo location of the agent.
    """
    if config["STATE"].getboolean("SETUP_STATUS"):
        raise HTTPException(status_code=400, detail={"status": "error", "error": "SETUP_ALREADY_DONE"})

    secret = secrets.token_hex(64)

    config["STATE"]["AGENT_NAME"] = setup_data.name
    config["STATE"]["AGENT_ID"] = setup_data.id
    config["STATE"]["AGENT_SECRET"] = secret
    config["STATE"]["SETUP_STATUS"] = "True"
    with open(CONFIG_PATH, 'w') as configfile:
        config.write(configfile)

    response = {
        "status": "ok",
        "data": {
            "secret": secret,
            "name": setup_data.name,
            "id": setup_data.id,
            "meta": requests.get(
                f'https://api.ipgeolocation.io/ipgeo?apiKey={config["API"]["IP_GEOLOCATION_API_KEY"]}').json()
        }
    }
    response["data"]["meta"]["latitude"] = float(response["data"]["meta"]["latitude"])
    response["data"]["meta"]["longitude"] = float(response["data"]["meta"]["longitude"])
    return response


class TraceData(BaseModel):
    url: str = Field(title="Request url", min_length=11)
    headers: Optional[dict] = Field(default={}, title="Request headers")
    data: Optional[str] = Field(default="", title="Request body data")
    method: Optional[str] = Field(default="get", title="Request method", min_length=3)


@app.post("/trace")
async def tracer(data: TraceData, secret: str = Header("")):
    """
    Main tracer method. Request will be authenticated with the secret key provided on setup.
    An empty result dictionary will be returned in case the website didn't respond or something failed with pycurl

    :param data: The data needed for tractus to make the request such as body, method, header ant etc.
    :param secret: secret key return by setup.
    :return: Trace result.
    """
    if not secret or secret != config["STATE"].get("AGENT_SECRET", ""):
        raise HTTPException(status_code=403, detail={"status": "error", "error": "Access denied"})

    if data.data == "":
        data.data = None
    try:
        trace = Tracer(
            url=data.url,
            method=data.method,
            headers=data.headers,
            data=data.data,
            timeout=11
        ).trace()
    except pycurl.error as e:
        # return an empty result dictionary if something went wrong.
        return TraceResult().as_dict()
    except Exception as e:
        return {"status": "error", "error": str(e)}, 500
    return trace.as_dict()


@app.get("/test")
async def test():
    return {"test": "ok"}
