FROM python:3.12-slim

WORKDIR /app

COPY . /app

# There's no easy way to first install requirements and then the package itself, so
# do it together: https://rye.astral.sh/guide/docker/
RUN pip install --no-cache-dir -r requirements.lock

CMD ["python", "src/eightify/cloud_app.py"]