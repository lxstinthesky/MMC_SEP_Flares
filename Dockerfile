FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY ./Code ./Code
COPY ./Cache/flare_list ./Cache/flare_list
COPY ./Cache/SolarMACH ./Cache/SolarMACH
COPY ./Cache/images ./Cache/images

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "Code/streamlit/app.py", "--server.port=8501", "--server.address=0.0.0.0"]