#!/bin/bash
# Create the Secret once; preserve it on subsequent deployments.
set -euo pipefail
cd "$(dirname "$0")"
kubectl apply -f namespace.yml
if kubectl get secret kornilov-secrets -n kornilov-ns >/dev/null 2>&1; then
    echo 'kornilov-secrets already exists; keeping its values.'
    exit 0
fi
read -rsp 'Password for the new PostgreSQL instance: ' DB_PASSWORD
printf '\n'
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')
kubectl create secret generic kornilov-secrets -n kornilov-ns \
    --from-literal=DB_PASSWORD="$DB_PASSWORD" \
    --from-literal=SECRET_KEY="$SECRET_KEY"
unset DB_PASSWORD SECRET_KEY
