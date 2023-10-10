ARG PYTHON_VERSION=3.9-slim-buster

# define an alias for the specfic python version used in this file.
FROM python:${PYTHON_VERSION} as python

# Python build stage
FROM python as python-build-stage

ARG BUILD_ENVIRONMENT=local

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  # dependencies for kcc
  libpng-dev \
  libjpeg-dev \
  sqlite3 \
  p7zip-full \
  unrar-free \
  wget \
  curl

# Requirements are installed here to ensure they will be cached.
COPY ./kcc-5.6.3/requirements.txt ./kcc-5.6.3/
COPY ./manga_web/requirements .

# Create Python Dependency and Sub-Dependency Wheels.
RUN --mount=type=cache,target=/root/.cache/pip \
  pip wheel --wheel-dir /usr/src/app/wheels  \
  -r ${BUILD_ENVIRONMENT}.txt

RUN cd kcc-5.6.3 \
  --mount=type=cache,target=/root/.cache/pip \
  pip wheel --wheel-dir /usr/src/app/wheels  \
  -r requirements.txt

# Python 'run' stage
FROM python as python-run-stage

ARG BUILD_ENVIRONMENT=local
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV BUILD_ENV ${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

# Install required system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
  # psycopg2 dependencies
  libpq-dev \
  # Translations dependencies
  gettext \
  wget \
  curl \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# All absolute dir copies ignore workdir instruction. All relative dir copies are wrt to the workdir instruction
# copy python dependency wheels from python-build-stage
COPY --from=python-build-stage /usr/src/app/wheels  /wheels/

# use wheels to install python dependencies
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
	&& rm -rf /wheels/

RUN wget 'https://github.com/benbjohnson/litestream/releases/download/v0.3.11/litestream-v0.3.11-linux-amd64.deb' \
  && dpkg -i litestream-v0.3.11-linux-amd64.deb \
  && rm litestream-v0.3.11-linux-amd64.deb

COPY ./compose/local/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/local/django/celery/worker/start /start-celeryworker
RUN sed -i 's/\r$//g' /start-celeryworker
RUN chmod +x /start-celeryworker

COPY ./compose/local/django/celery/beat/start /start-celerybeat
RUN sed -i 's/\r$//g' /start-celerybeat
RUN chmod +x /start-celerybeat

COPY ./compose/local/django/celery/flower/start /start-flower
RUN sed -i 's/\r$//g' /start-flower
RUN chmod +x /start-flower

COPY ./kindlegen /usr/local/bin
RUN chmod +x /usr/local/bin/kindlegen

COPY ./manga_crawler /crawler
# copy application code to WORKDIR
COPY ./manga_web ${APP_HOME}


ENTRYPOINT ["/entrypoint"]
