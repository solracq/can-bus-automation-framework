# Builds a reusable test environment for local Docker runs and Jenkins.
FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_PROGRESS_BAR=off \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/workspace/src

WORKDIR /workspace

COPY requirements.txt ./
RUN pip install --no-cache-dir --progress-bar off -r requirements.txt

COPY . .

RUN chmod +x scripts/setup_vcan.sh scripts/docker_entrypoint.sh scripts/run_tests_in_docker.sh

ENTRYPOINT ["./scripts/docker_entrypoint.sh"]
CMD ["pytest", "-q"]
