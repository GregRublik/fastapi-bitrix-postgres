FROM python:3.12.4

WORKDIR app/

COPY . .

RUN pip install -r requirements.txt

#RUN alembic revision --autogenerate -m 'initial' #создать миграцию

#RUN alembic upgrade head #применить миграцию

CMD python src/app.py
