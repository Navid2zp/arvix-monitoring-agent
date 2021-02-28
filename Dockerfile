FROM python:3

WORKDIR /home/agent

RUN apt-get install libcurl4-openssl-dev libssl-dev

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

CMD [ "python", "main.py" ]
