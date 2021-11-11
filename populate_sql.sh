#!/bin/bash
psql -U postgres < /timescale_ab/timescale_ab/data/cpu_usage.sql
psql -U postgres -d homework -c "\COPY cpu_usage FROM /timescale_ab/timescale_ab/data/cpu_usage.csv CSV HEADER"
