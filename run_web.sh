#!/bin/bash

echo "🌏 启动AI智能旅行规划助手 Web界面"
echo "===================================="

# 检查虚拟环境
if [ -d ".venv" ]; then
    echo "✅ 发现虚拟环境，正在激活..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "✅ 发现虚拟环境，正在激活..."
    source venv/bin/activate
else
    echo "⚠️  未检测到虚拟环境"
    echo "   建议先运行: bash setup.sh"
    echo ""
    read -p "是否继续使用系统Python? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 检查环境变量
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  未检测到 .env 配置文件"
    echo "   请先复制并配置 .env.example:"
    echo "   cp .env.example .env"
    echo "   然后编辑 .env 文件，填入你的 API Key"
    echo ""
    exit 1
fi


# 创建数据目录
mkdir -p data/plans
echo "✅ 数据目录已准备"

# 启动Streamlit
echo ""
echo "🚀 启动Web服务..."
echo ""
echo "   📱 访问地址: http://localhost:8501"
echo "   🛑 按 Ctrl+C 停止服务"
echo ""
echo "===================================="
echo ""

streamlit run frontend/app.py --server.port 8501 --server.address localhost
