FROM python:3.7-alpine

LABEL project="georchestra.org"
LABEL org.opencontainers.image.authors="jeanpommier@pi-geosolutions.fr"

COPY src /app/src
COPY requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

# Run as Alpine's Guest user
USER 405
CMD ["python", "/app/src/main.py"]
