FROM python:latest

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt
COPY app /usr/src/app

COPY etc /etc
VOLUME /etc/prometheus

CMD /usr/src/app/wrapper
