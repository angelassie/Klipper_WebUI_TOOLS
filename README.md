# Klipper WebUI Tools

为 Klipper 3D 打印系统扩展 WebUI 功能，支持 Mainsail 和 Fluidd。

## 功能特性

### 固件管理
- **固件编译** - 支持主板预设和自定义配置，一键编译 Klipper 固件
- **固件刷写** - 支持 DFU 模式自动刷写
- **固件下载** - 下载编译好的固件文件到本地

### 软件管理
- **KlipperScreen** - 触摸屏界面安装/更新
- **Crowsnest** - 摄像头流媒体安装/更新

### 多语言支持
- 中文界面
- 英文界面

## 安装方法

### 一键安装（推荐）

```bash
cd ~
git clone https://github.com/angelassie/Klipper_WebUI_TOOLS.git
cd Klipper_WebUI_TOOLS
chmod +x install.sh
./install.sh
```

### 手动安装

```bash
# 1. 克隆仓库
git clone https://github.com/angelassie/Klipper_WebUI_TOOLS.git

# 2. 复制 Moonraker 组件
cp Klipper_WebUI_TOOLS/moonraker/firmware.py ~/moonraker/moonraker/components/

# 3. 复制 WebUI 前端（根据你使用的 WebUI 选择）
# Mainsail 用户：
cp -r Klipper_WebUI_TOOLS/mainsail/dist/* ~/mainsail/

# Fluidd 用户：
cp -r Klipper_WebUI_TOOLS/fluidd/dist/* ~/fluidd/

# 4. 重启 Moonraker
sudo systemctl restart moonraker
```

## 更新方法

```bash
cd ~/Klipper_WebUI_TOOLS
git pull
./install.sh
```

## 卸载方法

```bash
cd ~/Klipper_WebUI_TOOLS
./uninstall.sh
```

## 系统要求

- Klipper 已安装
- Moonraker 已安装
- Mainsail 或 Fluidd 已安装
- Linux 系统（Raspberry Pi OS、Debian、Ubuntu 等）

## 许可证

本项目采用 [GPL-3.0](LICENSE) 协议开源。

## 致谢

- [Klipper](https://www.klipper3d.org/) - 3D 打印机固件
- [Moonraker](https://moonraker.readthedocs.io/) - API 服务器
- [Mainsail](https://mainsail.xyz/) - WebUI
- [Fluidd](https://docs.fluidd.xyz/) - WebUI
