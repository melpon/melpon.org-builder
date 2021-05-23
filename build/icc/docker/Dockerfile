FROM ubuntu:16.04

MAINTAINER melpon <shigemasa7watanabe+docker@gmail.com>

RUN apt-get update && \
    apt-get install -y software-properties-common apt-transport-https ca-certificates wget && \
    wget -O - https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB 2>/dev/null | apt-key add - && \
    add-apt-repository -y "deb https://apt.repos.intel.com/oneapi all main" && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        g++ \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
