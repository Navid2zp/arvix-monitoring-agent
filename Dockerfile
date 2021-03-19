FROM tiangolo/uvicorn-gunicorn:python3.8-alpine3.10

# Needed for the pycurl compilation
ENV PYCURL_SSL_LIBRARY=openssl

COPY ./requirements.txt .

RUN apk add -u --no-cache libcurl libstdc++ \
    && apk add -u --no-cache --virtual .build-deps g++ libffi-dev curl-dev \
    && pip install -r requirements.txt \
    && apk del --no-cache --purge .build-deps \
    && rm -rf /var/cache/apk/*

COPY . /app