FROM ubuntu:16.04

MAINTAINER melpon <shigemasa7watanabe+docker@gmail.com>

RUN apt-get update && \
    apt-get install -y \
      gcc \
      git \
      libc6-dev \
      libffi-dev \
      libgdbm-dev \
      libncursesw5-dev \
      libsqlite3-dev \
      libssl-dev \
      make \
      openssl \
      python-minimal \
      tk-dev \
      zlib1g-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

