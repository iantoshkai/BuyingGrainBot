FROM python:3.7.2-slim

WORKDIR /BuyingGrainBot

COPY requirements.txt /BuyingGrainBot/
RUN pip install --no-cache-dir --upgrade pip 
RUN pip install --no-cache-dir -r /BuyingGrainBot/requirements.txt
COPY . /BuyingGrainBot/

CMD export PYTHONPATH=/BuyingGrainBot/ && python3 ./app/bot.py
