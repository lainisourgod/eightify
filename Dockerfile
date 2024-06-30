FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.lock

EXPOSE 8000 8501

# TODO: change to composite app
CMD ["fastapi", "run", "src/eightify/main.py"]