FROM apache/superset:6.0.0

USER root
RUN /app/.venv/bin/python -m ensurepip \
    && /app/.venv/bin/python -m pip install --no-cache-dir 'trino[sqlalchemy]==0.336.0'

USER superset
