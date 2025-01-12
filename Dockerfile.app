# Use python 3.11 base Image
FROM python:3.11-slim

WORKDIR /app

COPY ./web  .env /app/web/

RUN pip3 install --no-cache-dir -r web/requirements.txt

# Set AWS secrets from host
RUN --mount=type=secret,id=aws,target=/root/.aws/credentials

# Create a volume for storing data parsed data
VOLUME ["/app/data"]

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "web/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
