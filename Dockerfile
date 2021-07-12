FROM python:3-alpine

LABEL project="georchestra.org"
LABEL org.opencontainers.image.authors="jeanpommier@pi-geosolutions.fr"

COPY src /app/src
COPY requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

CMD ["python", "/app/src/main.py"]