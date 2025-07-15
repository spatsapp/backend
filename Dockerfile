FROM python:3

WORKDIR /app

COPY ./spats_backend ./spats_backend
COPY ./requirements.txt .

RUN pip install -r requirements.txt

CMD [ "python3", "-m", "fastapi", "run", "spats_backend" ]
