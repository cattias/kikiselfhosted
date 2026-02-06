#!/bin/bash
echo "🚀 Starting Graceful Reboot..."

echo "⏸️ Scaling down ArgoCD..."
kubectl scale statefulset --all --replicas=0 -n argocd --timeout=10s
kubectl scale deployment --all --replicas=0 -n argocd --timeout=10s

NAMESPACES=$(kubectl get ns -o jsonpath='{.items[*].metadata.name}' | tr ' ' '\n' | grep -vE 'rook-ceph|kube-system|kube-public|kube-node-lease|metallb')

echo "⏸️ Scaling down Postgres and Redis operator ..."
kubectl scale deployment --all --replicas=0 -n postgres-operator --timeout=10s
kubectl scale statefulset --all --replicas=0 -n postgres-operator --timeout=10s
kubectl scale deployment --all --replicas=0 -n redis-operator --timeout=10s
kubectl scale statefulset --all --replicas=0 -n redis-operator --timeout=10s

echo "--- Dynamic Scale Down of all Apps ---"
for ns in $NAMESPACES; do
    echo "Processing namespace: $ns"
    # Scale deployments and statefulsets to 0
    kubectl scale deployment --all --replicas=0 -n "$ns" --timeout=10s
    kubectl scale statefulset --all --replicas=0 -n "$ns" --timeout=10s
done

echo "--- Freezing Databases (Postgres and Redis) ---"
# Delete the database pods in all namespaces
kubectl delete pods -n authentik -l cnpg.io/cluster=authentik-db
kubectl delete pods -n documents -l cnpg.io/cluster=paperless-db
kubectl delete pods -n mealie -l cnpg.io/cluster=mealie-db
kubectl delete pods -n photos -l cnpg.io/cluster=immich-db
kubectl delete pods -n vaultwarden -l cnpg.io/cluster=vaultwarden-db

kubectl scale sts immich-redis -n photos --replicas=0
kubectl scale sts paperless-redis -n documents --replicas=0

sleep 30

echo "🧹 Draining kikiserver ..."
# --disable-eviction is the key to bypassing those Paperless/Immich errors
kubectl drain kikiserver --ignore-daemonsets --delete-emptydir-data --force --grace-period=30 --disable-eviction
# For pods suck in Terminating
# kubectl get pods -A | grep Terminating | awk '{print "kubectl delete pod " $2 " -n " $1 " --force --grace-period=0"}' | sh

# 4. Stop K0s engine
echo "🛑 Stopping k0s..."
sudo k0s stop
# sudo modprobe -r ceph
# sudo modprobe -r libceph

echo "♻️ Rebooting now..."
sudo reboot