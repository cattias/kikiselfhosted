#!/bin/sh
sudo k0s stop
curl -sSLf https://get.k0s.sh | sudo sh
sudo k0s start