#!/bin/bash
NAMESPACE="bookstore-ns"
SERVICES=("book-deployment" "customer-deployment" "crm-service" "web-app-bff" "mobile-app-bff")

for SVC in "${SERVICES[@]}"
do
    echo "♻️ 重启 $SVC..."
    kubectl rollout restart deployment/$SVC -n $NAMESPACE
done