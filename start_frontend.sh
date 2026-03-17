#!/bin/bash
echo "🚀 啟動企業 AI 助理前端..."
cd frontend-vue

# 【重要】檢查 package-lock.json 是否變更
DEPS_HASH_FILE=".npm_deps_hash"
CURRENT_HASH=""

# 【修正 #6】改進 lock file 検查：優先看 package-lock.json，後退 package.json
if [ -f "package-lock.json" ]; then
    # 優先使用 package-lock.json
    LOCK_FILE="package-lock.json"
elif [ -f "package.json" ]; then
    # 退回使用 package.json
    LOCK_FILE="package.json"
else
    echo "⚠️ 警告：找不到 package-lock.json 或 package.json"
    LOCK_FILE=""
fi

if [ -n "$LOCK_FILE" ] && [ -f "$LOCK_FILE" ]; then
    # 支援 macOS 和 Linux 的 hash 検查
    if command -v md5sum &> /dev/null; then
        CURRENT_HASH=$(md5sum "$LOCK_FILE" | awk '{print $1}')
    elif command -v md5 &> /dev/null; then
        CURRENT_HASH=$(md5 -q "$LOCK_FILE")
    else
        CURRENT_HASH=$(shasum -a 256 "$LOCK_FILE" | awk '{print $1}')
    fi
fi

# 比較 hash，只在變更時重裝
if [ ! -f "$DEPS_HASH_FILE" ] || [ "$CURRENT_HASH" != "$(cat $DEPS_HASH_FILE 2>/dev/null)" ]; then
    echo "📦 依賴有變更，執行 npm install..."
    npm install
    echo "$CURRENT_HASH" > "$DEPS_HASH_FILE"
else
    echo "✅ 依賴無變更，跳過 npm install"
fi

npm run dev
