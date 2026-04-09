#!/bin/bash

# --- 配置区 ---
NAMESPACE="bookstore-ns"
# 定义需要部署的服务文件夹（确保名字和 Deployment 中的 app 标签一致）
# SERVICES=("book-service" "customer-service" "crm-service" "web-app-bff" "mobile-app-bff")
SERVICES=("web-app-bff")

echo "🚀 开始在 Namespace: $NAMESPACE 中执行深度部署..."

# 1. 确保 Namespace 存在
if ! kubectl get ns "$NAMESPACE" > /dev/null 2>&1; then
    echo "✨ 创建 Namespace: $NAMESPACE"
    kubectl create namespace "$NAMESPACE"
fi

# 2. 遍历文件夹并部署
for SERVICE in "${SERVICES[@]}"
do
    echo "----------------------------------------------------"
    if [ -d "$SERVICE" ]; then
        echo "📂 正在处理服务: $SERVICE"
        
        # 查找 yaml 文件
        count=$(ls "$SERVICE"/*.yaml 2>/dev/null | wc -l)
        
        if [ "$count" -gt 0 ]; then
            # A. 执行 Apply
            echo "📤 执行 kubectl apply..."
            kubectl apply -f "$SERVICE/" -n "$NAMESPACE"
            
            # B. 强制触发重启 (核心逻辑)
            # 这会强制 K8s 终止旧 Pod 并拉取最新的镜像
            echo "♻️  正在强制重启 $SERVICE 以刷新镜像缓存..."
            kubectl rollout restart deployment "$SERVICE" -n "$NAMESPACE"
            
            # C. 等待重启指令生效
            kubectl rollout status deployment "$SERVICE" -n "$NAMESPACE" --timeout=30s
        else
            echo "⚠️  警告: $SERVICE 目录下没有找到 .yaml 文件"
        fi
    else
        echo "❌ 错误: 找不到目录 $SERVICE"
    fi
done

echo "----------------------------------------------------"
echo "⏳ 部署指令已全部发送，当前 Pod 状态："
kubectl get pods -n "$NAMESPACE"

echo "🎉 所有服务已强制重启！"
echo "💡 请注意：确保你的 Deployment YAML 中设置了 'imagePullPolicy: Always'。"