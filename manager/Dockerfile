FROM python:3.9-slim

WORKDIR /app
COPY game_manager.py requirements.txt ./
COPY templates/ ./templates/
RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["python", "game_manager.py"]