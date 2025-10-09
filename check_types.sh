#!/bin/bash
# mypy 类型检查脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🔍 运行 mypy 类型检查..."
echo ""

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ 错误: 虚拟环境不存在${NC}"
    echo "请先运行: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 检查 mypy 是否安装
if ! .venv/bin/python -c "import mypy" 2>/dev/null; then
    echo -e "${RED}❌ 错误: mypy 未安装${NC}"
    echo "请先运行: .venv/bin/pip install mypy"
    exit 1
fi

# 运行类型检查
echo "📦 检查目标: app/"
echo "📋 配置文件: pyproject.toml"
echo ""

if .venv/bin/mypy app/ --pretty --config-file pyproject.toml; then
    echo ""
    echo -e "${GREEN}✅ 类型检查通过！${NC}"
    exit 0
else
    echo ""
    echo -e "${YELLOW}⚠️  类型检查发现问题，请修复后重新运行${NC}"
    exit 1
fi
