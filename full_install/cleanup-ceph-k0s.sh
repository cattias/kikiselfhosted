#!/bin/sh
kubectl patch secret rook-ceph-mon -p '{"metadata":{"finalizers":[]}}' --type=merge -n rook-ceph
kubectl patch configmap rook-ceph-mon-endpoints -p '{"metadata":{"finalizers":[]}}' --type=merge -n rook-ceph
kubectl patch cephblockpool replicapool -p '{"metadata":{"finalizers":[]}}' --type=merge -n rook-ceph
kubectl patch cephcluster rook-ceph -p '{"metadata":{"finalizers":[]}}' --type=merge -n rook-ceph
kubectl get crd | grep ceph | awk {'print $1}' | xargs -I {} kubectl patch crd {} -p '{"metadata":{"finalizers":[]}}' --type=merge -n rook-ceph
kubectl get crd | grep ceph | awk {'print $1}' | xargs -I {} kubectl delete crd {}

