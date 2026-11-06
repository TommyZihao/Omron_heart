#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
JDK=/Applications/Unity/Hub/Editor/6000.0.31f1/PlaybackEngines/AndroidPlayer/OpenJDK
BT="$PWD/tools/android-15"
PLATFORM="$PWD/tools/android-35/android.jar"
export JAVA_HOME="$JDK"
export PATH="$JDK/bin:$PATH"
mkdir -p build/classes build/dex
javac -source 8 -target 8 -bootclasspath "$PLATFORM:$BT/core-lambda-stubs.jar" -d build/classes src/cn/zihao/heartbeat/*.java
"$BT/d8" --lib "$PLATFORM" --min-api 31 --output build/dex build/classes/cn/zihao/heartbeat/*.class
"$BT/aapt" package -f -M AndroidManifest.xml -S res -A assets -I "$PLATFORM" -F build/unsigned.apk
(cd build/dex && zip -q -u ../unsigned.apk classes*.dex)
"$BT/zipalign" -f 4 build/unsigned.apk build/aligned.apk
if [ ! -f local-signing.jks ]; then keytool -genkeypair -keystore local-signing.jks -storepass android -keypass android -alias heartbeat -keyalg RSA -keysize 2048 -validity 10000 -dname 'CN=Heartbeat Local'; fi
"$BT/apksigner" sign --ks local-signing.jks --ks-pass pass:android --key-pass pass:android --out build/heartbeat.apk build/aligned.apk
"$BT/apksigner" verify build/heartbeat.apk
