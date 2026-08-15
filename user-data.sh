#!/bin/bash
# EC2 "User Data" bootstrap script (Amazon Linux 2023).
# Paste this into the "User data" field when launching the instance.
#
# Installs OS-level tools only: Docker, the Docker Compose CLI plugin, and
# Git. Nothing app-specific happens here on purpose — no repo clone, no
# .env, no `docker compose up`. Those steps involve secrets/private-repo
# credentials and should NOT go in User Data, since it's readable in plain
# text via the EC2 console and instance metadata. Do that part manually
# after SSHing in (see README.md's deployment notes).

set -euxo pipefail

dnf update -y
dnf install -y docker git

systemctl enable --now docker
usermod -aG docker ec2-user

# Note: both downloads below are for x86_64 instances. On a Graviton/ARM
# instance type (e.g. t4g.*), swap "x86_64"/"amd64" for "arm64" in both URLs.

mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# `dnf install docker` bundles an old buildx (0.12.x) that's too old for
# `docker compose build`/`up --build` (needs >=0.17.0). Installing a newer
# one here, in the same directory Docker checks before its own bundled
# one, so it takes priority without needing to touch/remove the original.
curl -SL https://github.com/docker/buildx/releases/download/v0.36.1/buildx-v0.36.1.linux-amd64 \
  -o /usr/local/lib/docker/cli-plugins/docker-buildx
chmod +x /usr/local/lib/docker/cli-plugins/docker-buildx
