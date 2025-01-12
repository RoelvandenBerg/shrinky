FROM pdok/gdal:0.8.3 AS base

# In case you need base debian dependencies install them here.
# RUN apt-get update && apt-get -y upgrade && apt-get install -y --no-install-recommends \
# #        TODO list depencies here \
#    && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# --- COMPILE-IMAGE ---
FROM base AS compile-image
ENV DEBIAN_FRONTEND=noninteractive

# Install dev dependencies
RUN apt-get update && apt-get -y upgrade && apt-get install -y --no-install-recommends \
        python3-pip && \
        apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade --no-cache-dir setuptools pip
RUN pip3 install --no-cache-dir pipenv

# Copy source
WORKDIR /code
COPY . /code

RUN PIPENV_VENV_IN_PROJECT=1 pipenv --three --site-packages
RUN pipenv sync

# --- BUILD IMAGE ---
FROM base AS build-image
WORKDIR /code

COPY --from=compile-image "/code/shrinky.egg-info/" "/code/shrinky.egg-info/"
COPY --from=compile-image "/code/shrinky" "/code/shrinky"
COPY --from=compile-image /code/.venv /code/.venv
COPY --from=compile-image "/usr/local/lib/python3.8/dist-packages" "/usr/local/lib/python3.8/dist-packages"

# Make sure we use the virtualenv:
ENV PATH="/code/.venv/bin:$PATH"

# Metadata params
ARG BUILD_DATE
ARG VERSION
ARG GIT_COMMIT_HASH

# Metadata
LABEL org.opencontainers.image.authors="William william.loosman@kadaster.nl" \
      org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.title="shrinky" \
      org.opencontainers.image.description="Shrinky shrinks geopackages to minimal size" \
      org.opencontainers.image.url="https://github.com/PDOK/shrinky" \
      org.opencontainers.image.vendor="PDOK" \
      org.opencontainers.image.source="https://github.com/PDOK/shrinky" \
      org.opencontainers.image.revision=$GIT_COMMIT_HASH \
      org.opencontainers.image.version=$VERSION

ENTRYPOINT [ "shrinky" ]