#!/bin/bash
# 清理临时浏览器数据目录

echo "🧹 清理临时浏览器数据..."

# 统计要删除的目录数量
count=$(find data/browser -maxdepth 1 -type d -name "tmp_user_data_*" | wc -l | tr -d ' ')

if [ "$count" -eq 0 ]; then
    echo "✓ 没有临时目录需要清理"
    exit 0
fi

echo "   发现 $count 个临时目录"

# 删除所有 tmp_user_data_* 目录
rm -rf data/browser/tmp_user_data_*

echo "✅ 清理完成"
