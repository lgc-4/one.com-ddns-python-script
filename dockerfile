FROM python:3-alpine AS base
FROM base AS builder

RUN mkdir /install
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN pip install --no-binary=:all: --target=/install -r /requirements.txt

FROM base
COPY --from=builder /install /usr/local

WORKDIR /app

COPY . .
RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "one_com_ddns.py"]
CMD []