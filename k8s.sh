#!/bin/bash

# --- 配置区 ---
NAMESPACE="bookstore-ns"
# 定义需要部署的服务文件夹
SERVICES=("book-service" "customer-service" "crm-service" "web-bff" "mobile-bff")

echo "☸️  开始在 Namespace: $NAMESPACE 中部署所有服务..."

# 1. 确保 Namespace 存在
kubectl get ns $NAMESPACE > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "创建 Namespace: $NAMESPACE"
    kubectl create namespace $NAMESPACE
fi

# 2. 遍历文件夹并部署
for SERVICE in "${SERVICES[@]}"
do
    echo "----------------------------------------------------"
    if [ -d "$SERVICE" ]; then
        echo "📂 进入文件夹: $SERVICE"
        
        # 查找文件夹下所有的 yaml 文件并执行
        # 如果你只想跑特定名字的文件，可以改成 kubectl apply -f "$SERVICE/deployment.yaml"
        count=$(ls $SERVICE/*.yaml 2>/dev/null | wc -l)
        
        if [ $count -gt 0 ]; then
            echo "🚀 正在执行 kubectl apply..."
            kubectl apply -f "$SERVICE/" -n $NAMESPACE
            echo "✅ $SERVICE 部署指令已发送"
        else
            echo "⚠️  警告: 在 $SERVICE 中没有找到 .yaml 文件"
        fi
    else
        echo "❌ 错误: 找不到目录 $SERVICE"
    fi
done

echo "----------------------------------------------------"
echo "⏳ 正在等待 Pod 启动状态..."
sleep 2
kubectl get pods -n $NAMESPACE

echo "🎉 自动化部署任务完成！"
echo "💡 提示: 使用 'kubectl get svc -n $NAMESPACE' 查看 LoadBalancer 地址。"