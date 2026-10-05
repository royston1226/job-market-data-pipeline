FROM python:3.11-slim
WORKDIR /project
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY pipeline pipeline
COPY sql sql
COPY app app
CMD ["python", "-m", "pipeline.run"]
