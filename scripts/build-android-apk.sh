#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export JAVA_HOME="${JAVA_HOME:-/home/box/android-tools/jdk}"
export ANDROID_HOME="${ANDROID_HOME:-/home/box/android-tools/sdk}"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export PATH="$JAVA_HOME/bin:$PATH"
cd "$ROOT/apps/android"
npm install
export VITE_API_BASE="${VITE_API_BASE:-https://sitemixhk.com/winci-api}"
echo "VITE_API_BASE=$VITE_API_BASE"
npm run build:web
npx cap sync android
echo "sdk.dir=$ANDROID_HOME" > android/local.properties
cd android
./gradlew assembleDebug
OUT="$ROOT/dist"
mkdir -p "$OUT"
cp -f app/build/outputs/apk/debug/app-debug.apk "$OUT/WinCi.apk"
echo "APK → $OUT/WinCi.apk"
ls -lh "$OUT/WinCi.apk"
