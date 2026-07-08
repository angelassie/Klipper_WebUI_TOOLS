#!/bin/bash
# Klipper WebUI Tools - 安装脚本
# 适用于 Mainsail 和 Fluidd
# GitHub: https://github.com/angelassie/Klipper_WebUI_TOOLS

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 检测 WebUI 类型
detect_webui() {
    if [ -d "$HOME/mainsail" ]; then
        echo "mainsail"
    elif [ -d "$HOME/fluidd" ]; then
        echo "fluidd"
    else
        echo "none"
    fi
}

# 检测系统环境
check_environment() {
    print_info "检测系统环境..."

    # 检测 Klipper
    if [ ! -d "$HOME/klipper" ]; then
        print_error "未找到 Klipper 安装目录: ~/klipper"
        print_error "请先安装 Klipper: https://www.klipper3d.org/Installation.html"
        exit 1
    fi
    print_success "检测到 Klipper: ~/klipper"

    # 检测 Moonraker
    if [ ! -d "$HOME/moonraker" ]; then
        print_error "未找到 Moonraker 安装目录: ~/moonraker"
        print_error "请先安装 Moonraker: https://moonraker.readthedocs.io/en/latest/Installation/"
        exit 1
    fi
    print_success "检测到 Moonraker: ~/moonraker"

    # 检测 WebUI
    WEBUI=$(detect_webui)
    if [ "$WEBUI" = "none" ]; then
        print_error "未找到 Mainsail 或 Fluidd"
        print_error "请先安装 Mainsail 或 Fluidd"
        exit 1
    fi
    print_success "检测到 WebUI: $WEBUI"
}

# 配置 sudoers 免密权限
configure_sudoers() {
    print_info "配置 sudo 免密权限..."

    local username=$(whoami)
    local sudoers_file="/etc/sudoers.d/klipper-tools"

    # 检查是否已配置
    if [ -f "$sudoers_file" ]; then
        print_info "sudoers 配置已存在，跳过"
        return 0
    fi

    # 检查 sudo 权限
    if ! sudo -n true 2>/dev/null; then
        print_warning "需要输入 sudo 密码来配置免密权限"
        echo "请输入 sudo 密码（输入时不显示）:"
    fi

    # 创建 sudoers 配置
    {
        echo "# Klipper WebUI Tools - sudo 免密配置"
        echo "# 此文件允许当前用户执行以下命令而无需输入密码"
        echo "$username ALL=(ALL) NOPASSWD: /usr/bin/dfu-util"
        echo "$username ALL=(ALL) NOPASSWD: /usr/bin/make"
        echo "$username ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart moonraker"
        echo "$username ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart klipper"
    } | sudo tee "$sudoers_file" > /dev/null

    # 设置正确的权限
    sudo chmod 440 "$sudoers_file"

    print_success "sudoers 配置完成"
    print_info "允许的命令:"
    echo "  - dfu-util (固件刷写)"
    echo "  - make (编译固件)"
    echo "  - systemctl restart moonraker"
    echo "  - systemctl restart klipper"
}

# 安装 Moonraker 组件
install_moonraker_component() {
    print_info "安装 Moonraker 固件组件..."

    # 备份原文件
    if [ -f "$HOME/moonraker/moonraker/components/firmware.py" ]; then
        print_warning "备份原 firmware.py..."
        cp "$HOME/moonraker/moonraker/components/firmware.py" \
           "$HOME/moonraker/moonraker/components/firmware.py.bak"
    fi

    # 复制新文件
    cp "$SCRIPT_DIR/moonraker/firmware.py" \
       "$HOME/moonraker/moonraker/components/firmware.py"

    print_success "Moonraker 组件安装完成"
}

# 安装 WebUI 前端
install_webui() {
    print_info "安装 $WEBUI 前端..."

    local webui_dir="$HOME/$WEBUI"
    local src_dir="$SCRIPT_DIR/$WEBUI/dist"

    # 备份原目录
    if [ -d "$webui_dir" ]; then
        print_warning "备份原 $WEBUI 目录..."
        if [ -d "${webui_dir}.bak" ]; then
            rm -rf "${webui_dir}.bak"
        fi
        mv "$webui_dir" "${webui_dir}.bak"
    fi

    # 创建新目录
    mkdir -p "$webui_dir"

    # 复制文件
    cp -r "$src_dir"/* "$webui_dir/"

    # 复制主板数据库
    if [ -f "$SCRIPT_DIR/mcu_boards.csv" ]; then
        cp "$SCRIPT_DIR/mcu_boards.csv" "$webui_dir/"
    fi

    print_success "$WEBUI 前端安装完成"
}

# 设置权限
set_permissions() {
    print_info "设置权限..."

    local webui_dir="$HOME/$WEBUI"
    chmod -R 755 "$webui_dir" 2>/dev/null || true

    print_success "权限设置完成"
}

# 添加 Moonraker 配置
add_moonraker_config() {
    print_info "检查 Moonraker 配置..."

    local moonraker_conf="$HOME/printer_data/config/moonraker.conf"
    if [ ! -f "$moonraker_conf" ]; then
        moonraker_conf="$HOME/moonraker/moonraker.conf"
    fi

    if [ -f "$moonraker_conf" ]; then
        # 检查是否已有 [firmware] 配置
        if ! grep -q "^\[firmware\]" "$moonraker_conf" 2>/dev/null; then
            print_info "添加 [firmware] 配置..."
            echo "" >> "$moonraker_conf"
            echo "[firmware]" >> "$moonraker_conf"
            echo "klipper_path: ~/klipper" >> "$moonraker_conf"
            echo "restart_klipper: False" >> "$moonraker_conf"
            print_success "配置已添加"
        else
            print_info "[firmware] 配置已存在，跳过"
        fi
    else
        print_warning "未找到 moonraker.conf，请手动添加配置"
    fi
}

# 重启 Moonraker 服务
restart_moonraker() {
    print_info "重启 Moonraker 服务..."

    if systemctl is-active --quiet moonraker; then
        sudo systemctl restart moonraker
        print_success "Moonraker 已重启"
    else
        print_warning "Moonraker 服务未运行，请手动启动"
    fi
}

# 显示安装结果
show_result() {
    echo ""
    echo "=========================================="
    print_success "安装完成!"
    echo "=========================================="
    echo ""
    echo "安装的组件:"
    echo "  - Moonraker 固件组件: ~/moonraker/moonraker/components/firmware.py"
    echo "  - WebUI 前端: ~/$WEBUI/"
    echo ""
    echo "访问 WebUI:"
    echo "  http://$(hostname -I | awk '{print $1}'):80"
    echo ""
    echo "功能说明:"
    echo "  - 固件编译: 选择主板型号，一键编译"
    echo "  - 固件刷写: 支持 DFU 模式刷写"
    echo "  - 固件下载: 下载编译好的固件文件"
    echo "  - 软件管理: 安装/更新 KlipperScreen、Crowsnest"
    echo ""
    echo "更新方法:"
    echo "  cd ~/${PWD##*/}"
    echo "  git pull"
    echo "  ./install.sh"
    echo ""
}

# 主函数
main() {
    echo ""
    echo "=========================================="
    echo "  Klipper WebUI Tools 安装脚本"
    echo "  GitHub: https://github.com/angelassie/Klipper_WebUI_TOOLS"
    echo "=========================================="
    echo ""

    check_environment
    configure_sudoers
    install_moonraker_component
    install_webui
    set_permissions
    add_moonraker_config
    restart_moonraker
    show_result
}

# 运行主函数
main
