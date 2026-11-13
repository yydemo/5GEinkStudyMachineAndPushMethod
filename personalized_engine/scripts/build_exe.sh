#!/usr/bin/env bash
# 使用 PyInstaller 将 CLI 打包为单文件可执行程序。
# 产物位于 dist/，已由 .gitignore 忽略，请勿提交二进制文件。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 -m pip install -e ".[exe]"

# GNU/Linux 与 macOS 使用冒号分隔 --add-data；Windows 请改为 "config.yaml;."
python3 -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --name eink-studyroom \
  --console \
  --add-data "config.yaml:." \
  --hidden-import src.cli \
  --hidden-import src.main \
  --hidden-import src.studyroom \
  src/cli.py

echo
echo "打包完成：${ROOT}/dist/eink-studyroom"
echo "请勿将 dist/ 或 build/ 中的二进制提交到仓库。"
