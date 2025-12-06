#!/bin/sh
kubectl scale deployment -n arr prowlarr --replicas=0
kubectl scale deployment -n arr lidarr --replicas=0
kubectl scale deployment -n arr radarr --replicas=0
kubectl scale deployment -n arr bazarr --replicas=0
kubectl scale deployment -n arr sonarr --replicas=0
kubectl scale deployment -n arr metube --replicas=0
kubectl scale deployment -n arr sabnzbd --replicas=0
