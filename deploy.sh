#!/bin/bash
# NSU Library Dashboard — 打包部署脚本
# Usage: bash deploy.sh

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT="nsu-library-dashboard.tar.gz"

echo "=========================================="
echo "  NSU Library Dashboard — 打包"
echo "=========================================="

# 创建临时目录
TMP_DIR=$(mktemp -d)
DEST="$TMP_DIR/nsu-library-dashboard"
mkdir -p "$DEST"

echo "[1/5] 复制应用代码..."
cp -r "$PROJECT_DIR/app" "$DEST/"
cp "$PROJECT_DIR/run.py" "$DEST/"
cp "$PROJECT_DIR/requirements.txt" "$DEST/"
cp "$PROJECT_DIR/Dockerfile" "$DEST/"
cp "$PROJECT_DIR/docker-compose.yml" "$DEST/"

echo "[2/5] 复制预计算数据..."
cp -r "$PROJECT_DIR/cache" "$DEST/"

echo "[3/5] 复制数据文件..."
mkdir -p "$DEST/data"
cp "$PROJECT_DIR/data/access records.xlsx" "$DEST/data/"
cp "$PROJECT_DIR/data/borrows.xlsx" "$DEST/data/"
cp "$PROJECT_DIR/data/returns.xlsx" "$DEST/data/"
cp "$PROJECT_DIR/data/students.xlsx" "$DEST/data/"
cp "$PROJECT_DIR/data/bookclassifications.xlsx" "$DEST/data/"

echo "[4/5] 打包 $OUTPUT..."
cd "$TMP_DIR"
tar -czf "$PROJECT_DIR/$OUTPUT" nsu-library-dashboard/

echo "[5/5] 清理临时文件..."
rm -rf "$TMP_DIR"

# 计算文件大小
SIZE=$(du -h "$PROJECT_DIR/$OUTPUT" | cut -f1)

echo ""
echo "=========================================="
echo "  打包完成！"
echo "=========================================="
echo "  文件: $OUTPUT"
echo "  大小: $SIZE"
echo ""
echo "  部署步骤："
echo "  1. 上传 $OUTPUT 到服务器"
echo "  2. tar -xzf $OUTPUT"
echo "  3. cd nsu-library-dashboard"
echo "  4. docker compose up -d --build"
echo "  5. 访问 http://服务器IP:8000"
echo "=========================================="
