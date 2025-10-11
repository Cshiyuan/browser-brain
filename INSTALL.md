# 安装指南

## 环境要求

- Python >= 3.11, < 3.14
- pip >= 21.0

## 安装步骤

### 1. 创建虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
```

### 2. 安装依赖

```bash
# 安装生产依赖
pip install -e .

# 安装开发依赖（包含 pylint, mypy）
pip install -e ".[dev]"
```

### 3. 安装 Playwright 浏览器

```bash
playwright install chromium
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key
```

## 验证安装

```bash
# 检查依赖
pip list | grep browser-use

# 运行类型检查
./check_types.sh

# 启动应用
./run_web.sh
```

## 更新依赖

```bash
# 更新所有依赖到最新兼容版本
pip install -e ".[dev]" --upgrade

# 查看已安装版本
pip list
```

## 卸载

```bash
pip uninstall browser-brain -y
deactivate
rm -rf .venv
```

## 常见问题

### Q: pip install -e . 是什么意思？
A: `-e` 表示"可编辑模式"（editable mode），修改代码后无需重新安装。

### Q: 为什么使用 pyproject.toml？
A: `pyproject.toml` 是 Python 现代标准（PEP 621），统一管理项目配置和依赖。

### Q: 如何添加新依赖？
A: 编辑 `pyproject.toml` 的 `dependencies` 列表，然后运行 `pip install -e .`。
