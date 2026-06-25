FROM python:3.12-slim

WORKDIR /opt/claude-ios-repair

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY repair_site ./repair_site
