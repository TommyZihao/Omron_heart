# 欧姆龙心跳联动 · Omron Heart

心电贴 ECG-D01M01 → Android 手机 BLE → 心搏检测 → 热点 UDP → ESP32 心跳灯 / M5StickS3 波形与振动。手机内置网页、音乐和图标，可脱离电脑运行。

## 文件

- `android/`：原生 Android Java 源码及离线界面；构建说明见 android/README.md。
- `releases/heartbeat.apk`：重新构建并验证签名的公开演示 APK。
- `esp32_led/`：ESP32 无线 LED 固件源码，GPIO4 外接 LED，GPIO2 板载 LED。
- `stick_vibrator/`：M5StickS3 无线波形及振动固件源码，依赖 M5Unified。
- `firmware/`：编译后的固件及分区文件，若提供 merged.bin 可使用 esptool 在地址 0x0 烧录。
- `wireless/*_usb.ino`：早期 USB 串口固件备份。
- `server*.py`、`wireless_bridge.py`、`web/`：电脑端接收及网页实现。

## 演示配置

热点名称 `OmronHeartDemo`，密码 `change-this-password`，须启用 2.4 GHz。公开版 App 和两份无线固件统一使用演示令牌 `omron-heart-demo-change-me`。实际使用请更换热点参数和配对令牌并重新构建；该演示参数不提供保密性。原现场凭据和签名私钥不在仓库中。

公开 APK 使用新签名，不能覆盖旧签名安装；安装前请自行保存旧版所需数据。演示固件须与公开版 App 配套，不能直接与原现场固件配对。

## 构建

Android：安装 JDK 17、Android API 35 和 Build Tools 35，按 `android/build.sh` 配置工具路径后执行 `bash android/build.sh`。

ESP32：`arduino-cli compile --fqbn esp32:esp32:esp32 esp32_led`

StickS3：`arduino-cli compile --fqbn m5stack:esp32:m5stack_sticks3 stick_vibrator`

电脑端需要 Python、bleak、aiohttp、pyserial，具体启动及版本行为以源码为准。不要同时运行多个蓝牙控制端或 UDP 分发器。

本项目用于实验展示；心搏检测未经过医学标注验证，不能用于诊断。
