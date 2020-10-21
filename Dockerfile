# syntax = docker/dockerfile:experimental
FROM python:3.7-buster as builder

# Install PyPI packages
COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && \
    pipenv install --system

FROM latonaio/pylib-lite:latest as runner

COPY --from=builder /usr/local/lib/python3.7/site-packages /usr/local/lib/python3.7/site-packages

ADD src/ .

CMD ["python3", "-u", "main.py"]
