#!/bin/sh
sudo docker buildx build \
  --platform linux/amd64 \
  -t kikiattias/soulsolid-plugins:latest \
  --push .
kubectl config use-context Server
kubectl rollout restart deployment soulsolid -n arr

