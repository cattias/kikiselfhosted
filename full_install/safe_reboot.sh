#!/bin/bash
echo "🚀 Starting Graceful Reboot..."

# 2. Stop ArgoCD Controller
echo "⏸️ Scaling down ArgoCD..."
kubectl -n argocd scale statefulset/argocd-application-controller --replicas=0

# 3. Drain the Node (Forcing past PDBs)
echo "🧹 Draining kikiserver ..."
# --disable-eviction is the key to bypassing those Paperless/Immich errors
kubectl drain kikiserver --ignore-daemonsets --delete-emptydir-data --force --grace-period=30 --disable-eviction
# For pods suck in Terminating
kubectl get pods -A | grep Terminating | awk '{print "kubectl delete pod " $2 " -n " $1 " --force --grace-period=0"}' | sh

# 4. Stop K0s engine
echo "🛑 Stopping k0s..."
sudo k0s stop

# 5. Flush NFS
echo "Unmapping Ceph RBD devices..."
for dev in /dev/rbd*; do
    if [ -b "$dev" ]; then
        echo "Unmapping $dev"
        rbd unmap "$dev" || true
    fi
done
sudo modprobe -r ceph
sudo modprobe -r libceph

echo "♻️ Rebooting now..."
sudo reboot

# after reboot
# kubectl uncordon kikiserver
# kubectl -n argocd scale statefulset/argocd-application-controller --replicas=1
# sudo systemctl restart tailscaled
