FROM python:3

WORKDIR /app

COPY ./backend ./backend
COPY ./requirements.txt .

RUN pip install -r requirements.txt

CMD [ "python3", "-m", "uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000" ]
