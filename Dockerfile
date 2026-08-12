# copied from https://fastapi.tiangolo.com/deployment/docker/#dockerfile
FROM python:3.14-slim
# the base image ships pip but no uv, so pull the uv binary from its official image (pinned)
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /uvx /bin/
# use the image's interpreter instead of downloading a managed CPython
ENV UV_PYTHON_DOWNLOADS=never
WORKDIR /code
COPY pyproject.toml README.md uv.lock ./
COPY ./src ./src
ARG VERSION=0.0.0
# install from the lockfile; the project's version is dynamic (hatch-vcs) and there is no
# .git in the build context, so SETUPTOOLS_SCM_PRETEND_VERSION supplies it
RUN SETUPTOOLS_SCM_PRETEND_VERSION=${VERSION} uv sync --locked --no-dev --no-editable
ENV PATH="/code/.venv/bin:$PATH"

EXPOSE 80

CMD ["fastapi", "run", "src/app/main.py", "--port", "80", "--forwarded-allow-ips", "*"]
# the settings for forwarded IPs are necessary if you deploy the App behind a reverse proxy
# see https://fastapi.tiangolo.com/advanced/behind-a-proxy/#enable-proxy-forwarded-headers
