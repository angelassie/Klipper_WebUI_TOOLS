#!/bin/bash
# Klipper WebUI Tools - 卸载脚本
# GitHub: https://github.com/angelassie/Klipper_WebUI_TOOLS

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 卸载 Moonraker 组件
uninstall_moonraker_component() {
    print_info "卸载 Moonraker 固件组件..."

    local firmware_file="$HOME/moonraker/moonraker/components/firmware.py"

    if [ -f "$firmware_file" ]; then
        # 检查是否是我们安装的版本
        if grep -q "Klipper WebUI Tools" "$firmware_file" 2>/dev/null; then
            rm "$firmware_file"
            print_success "已删除 firmware.py"
        else
            print_warning "firmware.py 不是本工具安装的，跳过删除"
        fi
    fi

    # 恢复备份
    if [ -f "${firmware_file}.bak" ]; then
        mv "${firmware_file}.bak" "$firmware_file"
        print_success "已恢复备份 firmware.py"
    fi
}

# 卸载 WebUI 前端（恢复备份）
uninstall_webui() {
    print_info "恢复 $WEBUI 前端..."

    local webui_dir="$HOME/$WEBUI"
    local backup_dir="${webui_dir}.bak"

    if [ -d "$backup_dir" ]; then
        rm -rf "$webui_dir"
        mv "$backup_dir" "$webui_dir"
        print_success "已恢复 $WEBUI 备份"
    else
        print_warning "未找到备份，跳过恢复"
    fi
}

# 移除 Moonraker 配置
remove_moonraker_config() {
    print_info "移除 Moonraker 配置..."

    local moonraker_conf="$HOME/printer_data/config/moonraker.conf"
    if [ ! -f "$moonraker_conf" ]; then
        moonraker_conf="$HOME/moonraker/moonraker.conf"
    fi

    if [ -f "$moonraker_conf" ]; then
        # 使用 sed 移除 [firmware] 配置块
        if grep -q "^\[firmware\]" "$moonraker_conf" 2>/dev/null; then
            sed -i '/^\[firmware\]/,/^$/d' "$moonraker_conf"
            print_success "已移除 [firmware] 配置"
        fi
    fi
}

# 重启 Moonraker 服务
restart_moonraker() {
    print_info "重启 Moonraker 服务..."

    if systemctl is-active --quiet moonraker; then
        sudo systemctl restart moonraker
        print_success "Moonraker 已重启"
    else
        print_warning "Moonraker 服务未运行"
    fi
}

# 显示卸载结果
show_result() {
    echo ""
    echo "=========================================="
    print_success "卸载完成!"
    echo "=========================================="
    echo ""
    echo "已移除:"
    echo "  - Moonraker 固件组件"
    echo "  - [firmware] 配置"
    echo ""
    echo "已恢复:"
    echo "  - $WEBUI 前端（从备份）"
    echo ""
}

# 主函数
main() {
    echo ""
    echo "=========================================="
    echo "  Klipper WebUI Tools 卸载脚本"
    echo "=========================================="
    echo ""

    WEBUI=$(detect_webui)
    if [ "$WEBUI" = "none" ]; then
        print_error "未检测到 Mainsail 或 Fluidd"
        exit 1
    fi

    print_info "检测到 WebUI: $WEBUI"
    echo ""

    # 确认卸载
    read -p "确定要卸载 Klipper WebUI Tools 吗？(y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        print_info "已取消卸载"
        exit 0
    fi

    uninstall_moonraker_component
    uninstall_webui
    remove_moonraker_config
    restart_moonraker
    show_result
}

main
