# copied from https://fastapi.tiangolo.com/deployment/docker/#dockerfile
FROM python:3.14-slim
WORKDIR /code
COPY pyproject.toml README.md ./
COPY ./src ./src
ARG VERSION=0.0.0
RUN SETUPTOOLS_SCM_PRETEND_VERSION=${VERSION} pip install .

EXPOSE 80

CMD ["fastapi", "run", "src/app/main.py", "--port", "80", "--forwarded-allow-ips", "*"]
# the settings for forwarded IPs are necessary if you deploy the App behind a reverse proxy
# see https://fastapi.tiangolo.com/advanced/behind-a-proxy/#enable-proxy-forwarded-headers