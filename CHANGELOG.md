# Changelog

All notable changes to this project will be documented in this file.

## [1.6.0] - 2025-10-12

### Changed

#### 依赖管理优化
- ✅ **统一使用 `pyproject.toml` 管理依赖**
  - 移除 `requirements.txt`（冗余）
  - 符合 Python 现代标准（PEP 621）
  - 支持 `pip install -e .` 可编辑模式安装
  - 增加开发依赖分组：`pip install -e ".[dev]"`

#### Browser-Use 更新
- ✅ **升级到 GitHub 最新版本 0.8.0**
  - 提交: `6d3e276875895649102de3903c01135e297100a8`
  - 从 PyPI 版本 0.7.10 升级到 GitHub 最新版
  - 直接从 GitHub 安装：`browser-use @ git+https://github.com/browser-use/browser-use.git@6d3e276`

#### 依赖版本调整
- 放宽版本限制以提高兼容性
- 修复 protobuf 版本冲突（降级到 5.29.5）
- 核心依赖更新：
  - `langchain-google-genai`: 2.1.12 → 2.0.10
  - `protobuf`: 6.32.1 → 5.29.5

### Added
- 📄 新增 `INSTALL.md` 安装指南
- 📄 新增 `CHANGELOG.md` 变更日志

### Removed
- ❌ 删除 `requirements.txt`（已迁移到 `pyproject.toml`）

---

## 安装方式变更

### 旧方式（已废弃）
```bash
pip install -r requirements.txt
```

### 新方式（推荐）
```bash
# 生产依赖
pip install -e .

# 包含开发工具
pip install -e ".[dev]"
```

---

## 核心依赖版本总结

| 依赖 | 版本 | 来源 |
|------|------|------|
| browser-use | 0.8.0 | GitHub@6d3e276 |
| playwright | 1.55.0 | PyPI |
| langchain | 0.3.27 | PyPI |
| streamlit | 1.50.0 | PyPI |
| protobuf | 5.29.5 | PyPI |

---

## 迁移指南

如果你之前使用 `requirements.txt`，请按以下步骤迁移：

1. **删除旧虚拟环境**（可选）
   ```bash
   rm -rf .venv
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **使用新方式安装**
   ```bash
   pip install -e ".[dev]"
   playwright install chromium
   ```

3. **验证安装**
   ```bash
   ./check_types.sh
   ./run_web.sh
   ```
