FROM python:3.9.5-alpine as builder
RUN apk add --no-cache libffi-dev cargo postgresql-dev && \
    pip install poetry
COPY . /timescale_ab
RUN cd timescale_ab && \
    poetry config virtualenvs.in-project true && \
    poetry install --no-dev

FROM timescale/timescaledb:latest-pg14-oss
# install python and link it where other image has it
RUN apk add --no-cache python3=3.9.5-r1 && \
    ln -s /usr/bin/python3.9 /usr/local/bin/python
COPY --from=builder /timescale_ab /timescale_ab
# puts this venv on the path
ENV PATH="/timescale_ab/.venv/bin:$PATH" 
RUN mv /timescale_ab/populate_sql.sh /docker-entrypoint-initdb.d/002_populate_hw.sh
