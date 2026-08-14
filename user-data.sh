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

mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
