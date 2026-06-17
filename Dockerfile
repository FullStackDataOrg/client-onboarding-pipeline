FROM python:3.11-slim
WORKDIR /workspace

RUN pip install --no-cache-dir \
    dagster==1.8.13 \
    dagster-webserver==1.8.13 \
    dagster-dbt==0.24.13 \
    dagster-duckdb==0.24.13 \
    dbt-duckdb==1.8.4 \
    pandas==2.2.3 \
    duckdb==1.1.3 \
    numpy>=1.26.0

RUN mkdir -p /workspace/dagster_home /workspace/data
