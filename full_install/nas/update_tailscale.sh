#!/bin/bash
TAILSCALE_VERSION=1.92.5

wget https://pkgs.tailscale.com/stable/tailscale_${TAILSCALE_VERSION}_amd64.tgz
tar xzvf tailscale_${TAILSCALE_VERSION}_amd64.tgz
cd tailscale_${TAILSCALE_VERSION}_amd64
sudo tailscale down
sudo systemctl stop tailscaled
sudo cp tailscale /usr/local/bin/
sudo cp tailscaled /usr/sbin/
sudo systemctl start tailscaled
sudo tailscale up
