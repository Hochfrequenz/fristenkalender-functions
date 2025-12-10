# copied from https://fastapi.tiangolo.com/deployment/docker/#dockerfile
FROM python:3.14
WORKDIR /code
RUN pip install .
COPY ./src/app /code/app

EXPOSE 80

CMD ["fastapi", "run", "app/main.py", "--port", "80","--forwarded-allow-ips", "*"]
# the settings for forwarded IPs are necessary if you deploy the App behind a reverse proxy
# see https://fastapi.tiangolo.com/advanced/behind-a-proxy/#enable-proxy-forwarded-headers