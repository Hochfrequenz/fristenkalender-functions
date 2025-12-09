FROM python:3.14-slim

WORKDIR /code

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ src/

EXPOSE 80

CMD ["fastapi", "run", "src/app/main.py", "--port", "80", "--forwarded-allow-ips", "*"]
