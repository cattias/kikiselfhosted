#!/bin/sh
ARGOCD_LATEST=$(curl -sSL https://api.github.com/repos/argoproj/argo-cd/releases/latest | grep '"tag_name":' | head -1 | awk -F '"' '{print $4}' | tr -d 'v')
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v$ARGOCD_LATEST/manifests/install.yaml
# kubectl patch deployment argocd-repo-server -n argocd --patch-file argocd-repo-server-deployment.yaml
kubectl patch configmap argocd-cmd-params-cm -n argocd --type merge -p '{"data":{"server.insecure":"true"}}'
ARGOCD_SERVER=$(kubectl get pod -n argocd -l app.kubernetes.io/name=argocd-server -o jsonpath='{.items[0].metadata.name}')
kubectl delete po -n argocd $ARGOCD_SERVER

# On the mac - update the client
# brew upgrade argocd