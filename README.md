# Klipper WebUI Tools

Extend Klipper 3D printer system with firmware build, flash, and software management features. Supports both Mainsail and Fluidd.

## Important: About Sudo Permissions

**This project requires sudo permissions for firmware flashing.**

### What is sudoers?

`sudoers` is a Linux system configuration that controls which users can run commands with root privileges (using `sudo`). This project configures sudoers to allow specific commands to run without entering a password.

### Why is a password required?

During installation, you will be prompted to enter your sudo password once. This password is used to:
- Configure sudoers permissions
- Restart system services (Moonraker, Klipper)

The password is **not stored** by this project. It is only used during the installation process.

### Security Risks

Configuring sudoers carries **inherent security risks**:
- Allows certain commands to execute without password verification
- If your system is compromised, an attacker could use these permissions
- The allowed commands include `make` (build tool) and `systemctl` (service control)

### Recommendation

**If you are concerned about security, do NOT install this project.**

This project is designed for:
- Personal 3D printer setups on trusted local networks
- Users who understand and accept the security implications
- Development and testing environments

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
- Chinese (中文)

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

## Disclaimer

**USE AT YOUR OWN RISK.**

This software is provided "as is" without warranty of any kind. The authors are not responsible for any damage to your 3D printer, computer, or other property that may result from using this software.

By installing this software, you acknowledge that:
1. You understand the security implications of configuring sudoers
2. You accept all risks associated with firmware flashing
3. You are solely responsible for any consequences of using this software

**This software is intended for educational and personal use only.**

## License

This project is licensed under the [GPL-3.0 License](LICENSE).

## Acknowledgments

- [Klipper](https://www.klipper3d.org/) - 3D printer firmware
- [Moonraker](https://moonraker.readthedocs.io/) - API server
- [Mainsail](https://mainsail.xyz/) - WebUI
- [Fluidd](https://docs.fluidd.xyz/) - WebUI
