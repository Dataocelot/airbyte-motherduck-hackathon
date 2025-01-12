# Use python 3.11 base Image
FROM python:3.11-slim

WORKDIR /app

COPY . /app/web

COPY ../.env /app

RUN pip3 --no-cache-dir -r requirements.txt

# Set AWS secrets from host
RUN --mount=type=secret,id=aws,target=/root/.aws/credentials

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
