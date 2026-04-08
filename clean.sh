#!/bin/bash
# A3 数据库清理脚本 - 适配最新 Schema

# --- 配置区 ---
DB_HOST="bookstore-db-dev-instance1.c2qxlb8d3arf.us-east-1.rds.amazonaws.com"
DB_USER="admin"
# 建议通过环境变量读取密码，或者在此处手动输入
echo ">>> 🧹 开始清理数据库..."

mysql -h "$DB_HOST" -P 3306 -u "$DB_USER" -p"12345678" <<EOF
-- 清理书籍数据库
USE books_db;
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE books;
SET FOREIGN_KEY_CHECKS = 1;

-- 清理客户数据库
USE customers_db;
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE customers;
-- TRUNCATE 会自动重置 AUTO_INCREMENT，让下一个用户 ID 重新从 1 开始
SET FOREIGN_KEY_CHECKS = 1;

SELECT '✅ 数据库已清空，主键计数器已重置' AS Result;
EOF