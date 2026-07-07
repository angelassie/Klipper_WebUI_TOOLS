# Klipper WebUI Tools

Extend Klipper 3D printer system with additional WebUI features. Supports Mainsail and Fluidd.

## Features

### Firmware Management
- **Firmware Build** - Board presets and custom configuration, one-click Klipper firmware build
- **Firmware Flash** - DFU mode auto-flash support
- **Firmware Download** - Download compiled firmware to local machine

### Software Management
- **KlipperScreen** - Touchscreen GUI install/update
- **Crowsnest** - Webcam streaming service install/update

### Multi-language Support
- English
- Chinese

## Installation

### One-Click Install (Recommended)

```bash
cd ~
git clone https://github.com/angelassie/Klipper_WebUI_TOOLS.git
cd Klipper_WebUI_TOOLS
chmod +x install.sh
./install.sh
```

### Manual Install

```bash
# 1. Clone repository
git clone https://github.com/angelassie/Klipper_WebUI_TOOLS.git

# 2. Copy Moonraker component
cp Klipper_WebUI_TOOLS/moonraker/firmware.py ~/moonraker/moonraker/components/

# 3. Copy WebUI frontend (choose based on your WebUI)
# For Mainsail users:
cp -r Klipper_WebUI_TOOLS/mainsail/dist/* ~/mainsail/

# For Fluidd users:
cp -r Klipper_WebUI_TOOLS/fluidd/dist/* ~/fluidd/

# 4. Restart Moonraker
sudo systemctl restart moonraker
```

## Update

```bash
cd ~/Klipper_WebUI_TOOLS
git pull
./install.sh
```

## Uninstall

```bash
cd ~/Klipper_WebUI_TOOLS
./uninstall.sh
```

## Requirements

- Klipper installed
- Moonraker installed
- Mainsail or Fluidd installed
- Linux system (Raspberry Pi OS, Debian, Ubuntu, etc.)

## License

This project is licensed under [GPL-3.0](LICENSE).

## Acknowledgments

- [Klipper](https://www.klipper3d.org/) - 3D printer firmware
- [Moonraker](https://moonraker.readthedocs.io/) - API server
- [Mainsail](https://mainsail.xyz/) - WebUI
- [Fluidd](https://docs.fluidd.xyz/) - WebUI
