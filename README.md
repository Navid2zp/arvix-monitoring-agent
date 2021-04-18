# arvix-monitoring-agent

## What is this?

This a standalone agent built with [FastAPI][2] to be used with [tractus][1] package. You can use this as an API server to trace and monitor websites by sending a request describing how you'd like to check the website.


## Install/Run

You'll need a ipgeolocation.io api key for setting up the agent. You can get a free api key from their website.

Set `IP_GEOLOCATION_API_KEY` in your config file.

### Docker:

The docker image is built on top of [uvicorn-gunicorn-docker][3] image (`python3.8-alpine3.10` version). You can check their github page for more running options.
```
docker run -d --name arvix-agent -e DEBUG=False -v /root/arvix_agent/config:/app/config -p 8181:80 docker.pkg.github.com/navid2zp/arvix-monitoring-agent/arvix-monitoring-agent
```

### uvicorn:

You need curl on your server. if you're using ubuntu, you need libcurl4-openssl-dev and libssl-dev installed.

```
pip install -r requirements.txt
uvicorn main:app
```


## Setup

You need to setup the agent on the first run to create a secret key. this secret key will be used for trace requests to authenticate your request.
To setup the agent, send a post request to `http://your-ip:selected-port/setup` with these data provided as a json payload:
```
{"name": "A-name-for-agent", "id": "1"}
```
You'll get a response containing the secret key and geo location data about the server that the agent is running on.

## Trace

You can send a request to `/trace` endpoint. You should describe your request with these fields (as json):

```python
class TraceData(BaseModel):
    url: str = Field(title="Request url", min_length=11)
    headers: Optional[dict] = Field(default={}, title="Request headers")
    data: Optional[str] = Field(default="", title="Request body data")
    method: Optional[str] = Field(default="get", title="Request method", min_length=3)
```

Example:

```json
{
    "url": "https://google.com",
    "method": "POST",
    "body: "{"name": "Navid", "last_name": "Zarepak"}",
    "headers": {"content-type": "application/json", "user-agent": "arvix-agent"}
}
```

## Swagger

FastAPI provides a swagger UI which is accessible at `http://your-ip:selected-port/docs`.


License
----
MIT

[1]: https://github.com/Navid2zp/tractus
[2]: https://fastapi.tiangolo.com
[3]: https://github.com/tiangolo/uvicorn-gunicorn-docker
