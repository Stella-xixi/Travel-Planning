# syntax=docker/dockerfile:1.7
ARG PYTHON_BASE_IMAGE=python:3.13.13-slim-bookworm

FROM ${PYTHON_BASE_IMAGE} AS dependencies

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/travel-planning/venv

RUN python -m venv "${VIRTUAL_ENV}"
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

WORKDIR /build
COPY requirements.txt ./
COPY packages/python/travel_planning_contracts ./packages/python/travel_planning_contracts
RUN python -m pip install --upgrade pip==25.1.1 && \
    python -m pip install --requirement requirements.txt && \
    python -m pip install --force-reinstall --no-deps ./packages/python/travel_planning_contracts


FROM ${PYTHON_BASE_IMAGE} AS runtime

ARG APP_BUILD_SHA=local
ARG APP_BUILD_CREATED_AT=unknown

ENV APP_BUILD_CREATED_AT=${APP_BUILD_CREATED_AT} \
    APP_BUILD_SHA=${APP_BUILD_SHA} \
    PATH=/opt/travel-planning/venv/bin:${PATH} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/backend:/app/agent \
    PYTHONUNBUFFERED=1

LABEL org.opencontainers.image.title="Travel-Planning V1 API and workers" \
      org.opencontainers.image.description="FastAPI, migration, Run worker, and outbox runtime" \
      org.opencontainers.image.revision=${APP_BUILD_SHA} \
      org.opencontainers.image.created=${APP_BUILD_CREATED_AT}

RUN apt-get update && \
    apt-get upgrade --yes --no-install-recommends && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd --gid 10001 travel-planning && \
    useradd --uid 10001 --gid 10001 --no-create-home --home-dir /nonexistent \
      --shell /usr/sbin/nologin travel-planning && \
    mkdir -p /app/data /app/logs && \
    chown -R 10001:10001 /app

WORKDIR /app
COPY --from=dependencies /opt/travel-planning/venv /opt/travel-planning/venv
COPY --chown=10001:10001 agent ./agent
COPY --chown=10001:10001 backend ./backend
COPY --chown=10001:10001 deploy/migrations ./deploy/migrations
COPY --chown=10001:10001 deploy/security/postgres-v1-grants.sql ./deploy/security/postgres-v1-grants.sql
COPY --chown=10001:10001 deploy/docker/healthcheck_v1.py ./deploy/docker/healthcheck_v1.py
COPY --chown=10001:10001 scripts/run_v1_outbox.py scripts/run_v1_worker.py \
  scripts/v1_apply_database_grants.py ./scripts/

USER 10001:10001
EXPOSE 38083

CMD ["python", "-m", "uvicorn", "travel_planning_api.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "38083"]
