FROM python:3.11.0-alpine AS i18n-build

COPY dev-requirements.txt /tmp/dev-requirements.txt
RUN pip install --no-cache-dir -r /tmp/dev-requirements.txt

COPY locales /tmp/locales
# Having no locales raises an error and is expected to fail, continuing anyway
RUN pybabel compile -D evgfilim1-userbot -d /tmp/locales || true

FROM python:3.11.0-slim AS wheel-build

WORKDIR /tmp

RUN apt update \
    && apt install -y --no-install-recommends gcc libc6-dev \
    && apt clean -y \
    && rm -rf /var/lib/apt/* /var/log/* /var/cache/*

# (2022-10-28) TgCrypto 1.2.4 doesn't have wheel for 3.11
RUN pip wheel --no-cache-dir 'TgCrypto==1.2.4' --wheel-dir /tmp/wheels

FROM jrottenberg/ffmpeg:5.1-ubuntu2004 AS runtime

WORKDIR /app

RUN useradd -Ud /app userbot \
    && mkdir -pm700 /data \
    && chown -R userbot:userbot /data \
    && apt update \
    && apt install -y --no-install-recommends gpg dirmngr gpg-agent \
    && echo 'deb https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu focal main' >>/etc/apt/sources.list \
    && echo 'deb-src https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu focal main' >>/etc/apt/sources.list \
    && apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv F23C5A6CF475977595C89F51BA6932366A755776 \
    && apt update \
    && apt install -y --no-install-recommends python3.11 python3.11-distutils libmagic1 curl \
    && { curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11; } \
    && apt autoremove -y gpg dirmngr gpg-agent curl --purge \
    && apt clean -y \
    && rm -rf /var/lib/apt/* /root/.cache /var/log/* /var/cache/*

VOLUME /data

COPY --from=wheel-build /tmp/wheels /tmp/wheels
COPY requirements.txt ./
RUN python3.11 -m pip install --no-cache-dir /tmp/wheels/* -r requirements.txt \
    && rm -rf /tmp/*

COPY --from=i18n-build /tmp/locales ./locales
COPY userbot ./userbot

USER userbot:userbot
ENTRYPOINT ["/usr/bin/env", "python3.11", "-m", "userbot"]
