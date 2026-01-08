#!/bin/sh
wget https://pkgs.tailscale.com/stable/tailscale_1.92.5_amd64.tgz
tar xzvf tailscale_1.92.5_amd64.tgz
sudo systemctl stop tailscaled
sudo cp tailscaled /usr/sbin/tailscaled 
sudo cp tailscale /usr/local/bin/tailscale
sudo systemctl start tailscaled
