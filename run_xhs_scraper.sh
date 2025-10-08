#!/bin/bash
# 小红书收集器便捷启动脚本

# 激活虚拟环境
source .venv/bin/activate

# 运行小红书收集器
python3 app/scrapers/run_xhs.py "$@"
