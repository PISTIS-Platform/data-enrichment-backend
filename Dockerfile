FROM python:3.8-slim

RUN apt-get update && apt-get install -y python3 python3-pip    

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /data-enrichment-backend/requirements.txt

WORKDIR /data-enrichment-backend
EXPOSE 8080

RUN pip install -r requirements.txt

COPY . .

WORKDIR /data-enrichment-backend/src 

ENTRYPOINT [ "python" ]

CMD [ "api.py" ]