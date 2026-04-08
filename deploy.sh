#!/bin/bash

# --- 配置区 ---
DOCKER_USER="linyul"  # 替换为你的 Docker Hub 用户名
TAG="latest"          # 你也可以手动改为 "v1", "v2" 等

# 定义需要构建的服务文件夹名称
SERVICES=("book-service" "customer-service" "crm-service" "web-bff" "mobile-bff")

echo "🚀 开始自动化构建与推送流程..."

for SERVICE in "${SERVICES[@]}"
do
    echo "----------------------------------------------------"
    echo "📦 正在处理服务: $SERVICE"
    
    # 检查文件夹是否存在
    if [ -d "$SERVICE" ]; then
        # 1. 构建镜像
        echo "🔨 Building image: $DOCKER_USER/$SERVICE:$TAG"
        docker build -t "$DOCKER_USER/$SERVICE:$TAG" "./$SERVICE"
        
        # 2. 推送镜像
        echo "📤 Pushing image to Docker Hub..."
        docker push "$DOCKER_USER/$SERVICE:$TAG"
        
        echo "✅ $SERVICE 处理完成!"
    else
        echo "⚠️ 警告: 找不到文件夹 $SERVICE，跳过。"
    fi
done

echo "----------------------------------------------------"
echo "🎉 所有镜像已成功推送到 Docker Hub!"
echo "💡 现在你可以去 EC2 上运行 kubectl rollout restart 了。"