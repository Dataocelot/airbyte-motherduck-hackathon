FROM python:3.11-slim-bullseye

WORKDIR /app

COPY ./web/requirements.txt .env ./
RUN pip install --cache-dir .cache/pip -r requirements.txt

COPY ./web /app/web
COPY ./helper /app/helper/
COPY ../pdfprocessor /app/pdfprocessor/


# Create a volume for storing data parsed data
VOLUME ["/app/data"]

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "web/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
