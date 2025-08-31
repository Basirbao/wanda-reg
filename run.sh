#!/bin/bash

cd "$(dirname "$0")"

# Wandb.ai自动注册工具启动脚本

# 检查uv虚拟环境是否存在
if [ ! -d ".venv" ]; then
    echo "未找到uv虚拟环境，正在创建..."
    uv venv
    echo "正在安装依赖..."
    uv pip install -r requirements.txt
fi

# 激活uv虚拟环境
source .venv/bin/activate

# 安装Playwright浏览器依赖
playwright install chromium

# 运行主程序
xvfb-run python main.py

# 保持终端窗口打开以便查看输出
if [ "$1" != "--auto-close" ]; then
    echo "按任意键退出..."
    read -n 1 -s
fi
