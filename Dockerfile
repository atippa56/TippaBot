FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*
COPY . .
RUN python3 setup_fast_market.py build_ext --inplace

EXPOSE 8080

CMD ["python3", "trading_bot.py"] 