FROM python:3.11-slim

ENV TINI_VERSION v0.19.0

ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini

RUN chmod +x /tini

WORKDIR /app

COPY pyproject.toml pdm.lock ./

COPY /simplecrud ./simplecrud

COPY main.py ./

RUN pip install pdm

RUN pdm install --prod -g -p .

ENTRYPOINT ["/tini", "--"]

ENTRYPOINT [ \
    "python", \
    "/app/main.py" \
  ]
