kubectl get secret admin-user -n argocd -o jsonpath="{.data.token}" | base64 -d

