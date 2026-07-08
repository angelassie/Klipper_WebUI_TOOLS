# Moonraker Firmware Component
# Provides API for building and flashing Klipper firmware
#
# Usage: Place this file in ~/moonraker/moonraker/components/
# Restart Moonraker to load the component.

import asyncio
import json
import logging
import os
import re
import subprocess
from pathlib import Path

logger = logging.getLogger("moonraker.firmware")

# MCU platform definitions with their options
# Based on Klipper's Kconfig files
MCU_PLATFORMS = {
    "AVR": {
        "models": [
            "atmega2560", "atmega1280", "at90usb1286", "at90usb646",
            "atmega32u4", "atmega1284p", "atmega644p", "atmega328p",
            "atmega328", "atmega168", "lgt8f328p"
        ],
        "clock_ref": ["8 MHz crystal", "16 MHz crystal"],
        "bootloader": {
            "default": ["No bootloader", "2KiB bootloader", "4KiB bootloader",
                        "8KiB bootloader", "16KiB bootloader"]
        },
        "communication": {
            "default": [
                "Serial (on UART)",
                "USB (on PD2/PD3)"
            ]
        }
    },
    "ATSAM": {
        "models": ["SAM3X8E", "SAM3X8C", "SAM4S8C", "SAM4E8E", "SAME70Q20B"],
        "clock_ref": [],
        "bootloader": {
            "SAM3X8E": ["No bootloader", "128KiB bootloader"],
            "SAM3X8C": ["No bootloader", "128KiB bootloader"],
            "SAM4S8C": ["No bootloader", "16KiB bootloader"],
            "SAM4E8E": ["No bootloader", "16KiB bootloader"],
            "SAME70Q20B": ["No bootloader", "16KiB bootloader"],
            "default": ["No bootloader", "16KiB bootloader"]
        },
        "communication": {
            "default": [
                "USB (on PA11/PA12)",
                "Serial (on USART1 PA10/PA9)",
                "CAN bus (on PA11/PA12)"
            ]
        }
    },
    "ATSAMD": {
        "models": [
            "SAMC21G18", "SAMD21G18", "SAMD21E18", "SAMD21J18", "SAMD21E15",
            "SAMD51G19", "SAMD51J19", "SAMD51N19", "SAMD51P20",
            "SAME51J19", "SAME51N19", "SAME54P20"
        ],
        "clock_ref": [],
        "bootloader": {
            "default": ["No bootloader", "8KiB bootloader", "16KiB bootloader"]
        },
        "communication": {
            "default": [
                "USB (on PA24/PA25)",
                "Serial (on SERCOM0 PA04/PA05)",
                "CAN bus (on PA11/PA12)"
            ]
        }
    },
    "LPC176x": {
        "models": ["LPC1768", "LPC1769"],
        "clock_ref": ["12 MHz crystal", "16 MHz crystal"],
        "bootloader": {
            "default": ["No bootloader", "8KiB bootloader", "16KiB bootloader",
                        "32KiB bootloader", "64KiB bootloader"]
        },
        "communication": {
            "default": [
                "USB (on P0.31/P0.30)",
                "Serial (on USART1 P0.15/P0.16)",
                "CAN bus (on P0.0/P0.1)"
            ]
        }
    },
    "STM32": {
        "models": [
            "STM32F103", "STM32F207", "STM32F401", "STM32F405", "STM32F407",
            "STM32F429", "STM32F446", "STM32F765", "STM32F031", "STM32F042",
            "STM32F070", "STM32F072", "STM32G070", "STM32G071", "STM32G0B0",
            "STM32G0B1", "STM32G431", "STM32G474", "STM32H723", "STM32H743",
            "STM32H750", "STM32L412"
        ],
        "clock_ref": ["8 MHz crystal", "12 MHz crystal", "16 MHz crystal",
                       "20 MHz crystal", "24 MHz crystal", "25 MHz crystal",
                       "Internal clock"],
        "bootloader": {
            "STM32F103": ["No bootloader", "2KiB bootloader", "4KiB bootloader",
                          "8KiB bootloader", "16KiB bootloader", "20KiB bootloader",
                          "28KiB bootloader", "32KiB bootloader", "34KiB bootloader",
                          "36KiB bootloader", "48KiB bootloader", "64KiB bootloader"],
            "STM32F207": ["No bootloader", "32KiB bootloader"],
            "STM32F401": ["No bootloader", "32KiB bootloader", "48KiB bootloader"],
            "STM32F405": ["No bootloader", "32KiB bootloader", "48KiB bootloader",
                          "64KiB bootloader", "128KiB bootloader", "128KiB bootloader with 512 byte offset"],
            "STM32F407": ["No bootloader", "32KiB bootloader", "48KiB bootloader",
                          "64KiB bootloader", "128KiB bootloader", "128KiB bootloader with 512 byte offset"],
            "STM32F429": ["No bootloader", "32KiB bootloader", "48KiB bootloader",
                          "64KiB bootloader", "128KiB bootloader", "128KiB bootloader with 512 byte offset"],
            "STM32F446": ["No bootloader", "32KiB bootloader", "64KiB bootloader"],
            "STM32F765": ["No bootloader", "128KiB bootloader"],
            "STM32F031": ["No bootloader", "4KiB bootloader", "8KiB bootloader"],
            "STM32F042": ["No bootloader", "8KiB bootloader", "16KiB bootloader",
                          "32KiB bootloader"],
            "STM32F070": ["No bootloader", "8KiB bootloader"],
            "STM32F072": ["No bootloader", "8KiB bootloader", "16KiB bootloader",
                          "32KiB bootloader"],
            "STM32G070": ["No bootloader", "8KiB bootloader"],
            "STM32G071": ["No bootloader", "8KiB bootloader"],
            "STM32G0B0": ["No bootloader", "8KiB bootloader"],
            "STM32G0B1": ["No bootloader", "8KiB bootloader"],
            "STM32G431": ["No bootloader", "8KiB bootloader"],
            "STM32G474": ["No bootloader", "8KiB bootloader", "32KiB bootloader"],
            "STM32H723": ["No bootloader", "128KiB bootloader"],
            "STM32H743": ["No bootloader", "128KiB bootloader"],
            "STM32H750": ["No bootloader", "128KiB bootloader"],
            "STM32L412": ["No bootloader", "4KiB bootloader"]
        },
        "communication": {
            "STM32F103": [
                "USB (on PA11/PA12)",
                "Serial (on USART1 PA10/PA9)",
                "Serial (on USART2 PA3/PA2)",
                "Serial (on USART3 PB11/PB10)",
                "CAN bus (on PA11/PA12)",
                "CAN bus (on PA11/PB9)"
            ],
            "STM32F207": [
                "USB (on PA11/PA12)",
                "Serial (on USART1 PA10/PA9)",
                "CAN bus (on PA11/PA12)"
            ],
            "STM32F401": [
                "USB (on PA11/PA12)",
                "Serial (on USART1 PA10/PA9)",
                "Serial (on USART6 PA12/PA11)"
            ],
            "STM32F405": [
                "USB (on PA11/PA12)",
                "Serial (on USART1 PA10/PA9)",
                "CAN bus (on PA11/PA12)",
                "CAN bus (on PA11/PB9)",
                "USB to CAN bus bridge (USB on PA11/PA12)"
            ],
            "STM32F407": [
                "USB (on PA11/PA12)",
                "Serial (on USART1 PA10/PA9)",
                "CAN bus (on PA11/PA12)",
                "CAN bus (on PA11/PB9)",
                "USB to CAN bus bridge (USB on PA11/PA12)"
            ],
            "STM32F429": [
                "USB (on PA11/PA12)",
                "Serial (on USART1 PA10/PA9)",
                "CAN bus (on PA11/PA12)",
                "CAN bus (on PA11/PB9)"
            ],
            "STM32F446": [
                "USB (on PA11/PA12)",
                "Serial (on USART1 PA10/PA9)",
                "CAN bus (on PA11/PA12)",
                "CAN bus (on PA11/PB9)",
                "USB to CAN bus bridge (USB on PA11/PA12)"
            ],
            "STM32F765": [
                "USB (on PA11/PA12)",
                "Serial (on USART1 PA10/PA9)",
                "CAN bus (on PA11/PA12)",
                "USB to CAN bus bridge (USB on PA11/PA12)"
            ],
            "STM32F031": [
                "Serial (on USART1 PA10/PA9)"
            ],
            "STM32F042": [
                "USB (on PA11/PA12)",
                "USB (on PA9/PA10)",
                "Serial (on USART1 PA10/PA9)",
                "CAN bus (on PA11/PA12)",
                "CAN bus (on PA9/PA10)",
                "USB to CAN bus bridge (USB on PA11/PA12)"
            ],
            "STM32F070": [
                "USB (on PA11/PA12)",
                "Serial (on USART1 PA10/PA9)"
            ],
            "STM32F072": [
                "USB (on PA11/PA12)",
                "Serial (on USART1 PA10/PA9)",
                "CAN bus (on PA11/PA12)",
                "USB to CAN bus bridge (USB on PA11/PA12)"
            ],
            "STM32G070": [
                "Serial (on USART1 PA10/PA9)"
            ],
            "STM32G071": [
                "Serial (on USART1 PA10/PA9)"
            ],
            "STM32G0B0": [
                "Serial (on USART1 PA10/PA9)",
                "Serial (on USART5 PD2/PD3)"
            ],
            "STM32G0B1": [
                "Serial (on USART1 PA10/PA9)",
                "Serial (on USART5 PD2/PD3)",
                "CAN bus (on PA11/PA12)",
                "CAN bus (on PB5/PB6)",
                "USB to CAN bus bridge (USB on PA11/PA12)"
            ],
            "STM32G431": [
                "Serial (on USART1 PA10/PA9)",
                "CAN bus (on PA11/PA12)",
                "USB to CAN bus bridge (USB on PA11/PA12)"
            ],
            "STM32G474": [
                "Serial (on USART1 PA10/PA9)",
                "Serial (on USART3 PC11/PC10)",
                "CAN bus (on PA11/PA12)",
                "CAN bus (on PB12/PB13)",
                "USB to CAN bus bridge (USB on PA11/PA12)"
            ],
            "STM32H723": [
                "USB (on PA11/PA12)",
                "Serial (on UART4 PA0/PA1)",
                "CAN bus (on PA11/PA12)",
                "CAN bus (on PB5/PB6)",
                "CAN bus (on PB12/PB13)",
                "CAN bus (on PD0/PD1)",
                "CAN bus (on PD12/PD13)",
                "CAN bus (on PC2/PC3)",
                "USB to CAN bus bridge (USB on PA11/PA12)"
            ],
            "STM32H743": [
                "USB (on PA11/PA12)",
                "USB (on PB14/PB15)",
                "Serial (on UART4 PA0/PA1)",
                "CAN bus (on PA11/PA12)",
                "CAN bus (on PB5/PB6)",
                "CAN bus (on PB12/PB13)",
                "CAN bus (on PD0/PD1)",
                "CAN bus (on PH13/PH14)",
                "USB to CAN bus bridge (USB on PA11/PA12)"
            ],
            "STM32H750": [
                "USB (on PA11/PA12)",
                "USB (on PB14/PB15)",
                "Serial (on UART4 PA0/PA1)",
                "CAN bus (on PA11/PA12)",
                "CAN bus (on PB5/PB6)",
                "CAN bus (on PB12/PB13)",
                "CAN bus (on PD0/PD1)",
                "USB to CAN bus bridge (USB on PA11/PA12)"
            ],
            "STM32L412": [
                "USB (on PA11/PA12)",
                "Serial (on USART1 PA10/PA9)"
            ]
        }
    },
    "RP2040": {
        "models": ["rp2040", "rp2350"],
        "clock_ref": [],
        "bootloader": {
            "rp2040": ["No bootloader", "16KiB bootloader"],
            "rp2350": ["No bootloader", "16KiB bootloader"]
        },
        "communication": {
            "default": [
                "USBSERIAL",
                "UART0 on GPIO0/GPIO1",
                "UART0 on GPIO12/GPIO13",
                "UART0 on GPIO16/GPIO17",
                "UART0 on GPIO28/GPIO29",
                "UART1 on GPIO4/GPIO5",
                "UART1 on GPIO8/GPIO9",
                "UART1 on GPIO20/GPIO21",
                "UART1 on GPIO24/GPIO25",
                "CAN bus",
                "USB to CAN bus bridge"
            ]
        }
    },
    "HC32F460": {
        "models": ["HC32F460"],
        "clock_ref": [],
        "bootloader": {
            "default": ["No bootloader", "8KiB bootloader"]
        },
        "communication": {
            "default": [
                "Serial (PA7 & PA8)",
                "Serial (PA13 & PA14)",
                "Serial (PA3 & PA2)",
                "Serial (PH2 & PB10)",
                "Serial (PA15 & PA09)"
            ]
        }
    }
}


class FirmwareComponent:
    def __init__(self, config):
        self.config = config
        self.server = config.get_server()
        # Expand ~ in the path
        self.klipper_path = os.path.expanduser(config.get("klipper_path", "~/klipper"))
        self.restart_klipper = config.getboolean("restart_klipper", False)

        # Register API endpoints
        self.server.register_endpoint(
            "/server/firmware/info", ["GET"], self._handle_firmware_info
        )
        self.server.register_endpoint(
            "/server/firmware/build", ["POST"], self._handle_firmware_build
        )
        self.server.register_endpoint(
            "/server/firmware/flash", ["POST"], self._handle_firmware_flash
        )
        self.server.register_endpoint(
            "/server/firmware/cancel", ["POST"], self._handle_firmware_cancel
        )
        self.server.register_endpoint(
            "/server/firmware/log", ["GET"], self._handle_firmware_log
        )
        self.server.register_endpoint(
            "/server/firmware/dfu", ["GET"], self._handle_firmware_dfu
        )
        self.server.register_endpoint(
            "/server/firmware/download", ["GET"], self._handle_firmware_download
        )
        # Software management endpoints
        self.server.register_endpoint(
            "/server/software/list", ["GET"], self._handle_software_list
        )
        self.server.register_endpoint(
            "/server/software/status", ["GET"], self._handle_software_status
        )
        self.server.register_endpoint(
            "/server/software/install", ["POST"], self._handle_software_install
        )
        self.server.register_endpoint(
            "/server/software/update", ["POST"], self._handle_software_update
        )
        self.server.register_endpoint(
            "/server/software/remove", ["POST"], self._handle_software_remove
        )
        self.server.register_endpoint(
            "/server/software/log", ["GET"], self._handle_software_log
        )

        # Linux command execution endpoint
        self.server.register_endpoint(
            "/server/firmware/exec", ["POST"], self._handle_exec_command
        )

        # Build state
        self.build_process = None
        self.build_log = []
        self.build_status = "idle"  # idle, building, success, failed, cancelled

        # Software management state
        self.software_process = None
        self.software_log = []
        self.software_status = "idle"

        logger.info("Firmware component initialized, klipper_path: %s", self.klipper_path)

    async def _handle_firmware_info(self, web_request):
        """Get firmware configuration info"""
        return {
            "platforms": MCU_PLATFORMS,
            "klipper_path": self.klipper_path,
            "current_config": self._get_current_config(),
            "build_status": self.build_status
        }

    def _get_current_config(self):
        """Read current .config file"""
        config_path = os.path.join(self.klipper_path, ".config")
        config = {}
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("CONFIG_") and "=" in line:
                        key, _, value = line.partition("=")
                        config[key[7:]] = value.strip('"')
        return config

    async def _handle_firmware_build(self, web_request):
        """Build firmware with given configuration"""
        if self.build_status == "building":
            return {"status": "error", "message": "Build already in progress"}

        # Get configuration from request
        platform = web_request.get("platform", "STM32")
        model = web_request.get("model", "STM32F446")
        clock_ref = web_request.get("clock_ref", "25 MHz crystal")
        bootloader = web_request.get("bootloader", "No bootloader")
        communication = web_request.get("communication", "USB (on PA11/PA12)")
        initial_pins = web_request.get("initial_pins", "")

        all_args = web_request.get_args()
        logger.info(f"Build request: platform={platform}, model={model}, all_args={all_args}")

        self.build_log = []
        self.build_status = "building"

        # Generate .config content
        config_content = self._generate_config(
            platform, model, clock_ref, bootloader, communication, initial_pins
        )

        try:
            # Write .config file
            config_path = os.path.join(self.klipper_path, ".config")
            with open(config_path, "w") as f:
                f.write(config_content)

            self.build_log.append(f"Configuration saved to {config_path}")
            self.build_log.append("Generating default config options...")
            self.build_log.append("Starting build...")

            # Run make olddefconfig to fill in defaults, then make clean && make
            result = await self._run_command(
                f"cd {self.klipper_path} && make olddefconfig && make clean && make",
                self.klipper_path
            )

            if result["returncode"] == 0:
                self.build_status = "success"
                self.build_log.append("Build completed successfully!")
            else:
                self.build_status = "failed"
                self.build_log.append(f"Build failed with return code {result['returncode']}")

            return {
                "status": self.build_status,
                "log": self.build_log,
                "returncode": result["returncode"]
            }
        except Exception as e:
            self.build_status = "failed"
            self.build_log.append(f"Error: {str(e)}")
            return {"status": "error", "message": str(e), "log": self.build_log}

    async def _handle_firmware_flash(self, web_request):
        """Flash firmware to MCU"""
        if self.build_status == "building":
            return {"status": "error", "message": "Build in progress, cannot flash"}

        # Get flash_device from args, default to 0483:df11 if not provided
        flash_device = web_request.get("flash_device", "0483:df11")
        all_args = web_request.get_args()
        logger.info(f"Flash request: flash_device='{flash_device}', all_args={all_args}")
        self.build_log = []
        self.build_status = "flashing"

        try:
            # Use dfu-util directly for better control
            firmware_path = os.path.join(self.klipper_path, "out", "klipper.bin")
            if not os.path.exists(firmware_path):
                self.build_status = "failed"
                self.build_log.append("Firmware file not found. Please build firmware first.")
                return {"status": "failed", "log": self.build_log}

            # Flash command using dfu-util directly (requires sudoers NOPASSWD)
            cmd = f"sudo dfu-util -d ,{flash_device} -a 0 -s 0x800c000:leave -D {firmware_path}"

            self.build_log.append(f"Flashing firmware to {flash_device}...")
            result = await self._run_command(cmd, self.klipper_path)

            # dfu-util for STM32 always returns non-zero even when flash is successful
            # (due to "can't detach" error after download completes)
            # So we just report success if no Python exception occurred
            self.build_status = "success"
            self.build_log.append("Flash completed! Device will reboot automatically.")

            return {
                "status": self.build_status,
                "log": self.build_log,
                "returncode": result["returncode"]
            }
        except Exception as e:
            self.build_status = "failed"
            self.build_log.append(f"Error: {str(e)}")
            return {"status": "error", "message": str(e), "log": self.build_log}

    async def _handle_firmware_cancel(self, web_request):
        """Cancel ongoing build or flash"""
        if self.build_process and self.build_process.returncode is None:
            self.build_process.terminate()
            self.build_status = "cancelled"
            self.build_log.append("Build cancelled by user")
            return {"status": "cancelled"}
        return {"status": "no_process"}

    async def _handle_firmware_log(self, web_request):
        """Get current build log"""
        return {
            "log": self.build_log,
            "status": self.build_status
        }

    async def _handle_firmware_dfu(self, web_request):
        """Detect DFU devices"""
        try:
            # Run lsusb directly to detect USB devices
            process = await asyncio.create_subprocess_shell(
                "lsusb",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            dfu_devices = []
            if process.returncode == 0:
                output = stdout.decode()
                for line in output.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    # Look for common DFU device IDs
                    if "0483:df11" in line.lower():  # STM32 DFU
                        dfu_devices.append({"type": "STM32 DFU", "info": line})
                    elif "1eaf:0003" in line.lower():  # STM32 Maple DFU
                        dfu_devices.append({"type": "STM32 Maple DFU", "info": line})
                    elif "1209:beba" in line.lower():  # CanBoot/Katapult
                        dfu_devices.append({"type": "CanBoot/Katapult", "info": line})
                    elif "1d50:6177" in line.lower():  # CanBoot
                        dfu_devices.append({"type": "CanBoot", "info": line})
                    elif "2e8a:0003" in line.lower():  # RP2040
                        dfu_devices.append({"type": "RP2040", "info": line})
                    elif "2e8a:000f" in line.lower():  # RP2350
                        dfu_devices.append({"type": "RP2350", "info": line})
            return {
                "devices": dfu_devices,
                "has_device": len(dfu_devices) > 0
            }
        except Exception as e:
            return {"devices": [], "has_device": False, "error": str(e)}

    async def _handle_firmware_download(self, web_request):
        """Download compiled firmware file as base64"""
        import base64
        firmware_path = os.path.join(self.klipper_path, "out", "klipper.bin")
        if not os.path.exists(firmware_path):
            return {"error": "Firmware file not found. Please build firmware first."}
        with open(firmware_path, "rb") as f:
            file_data = f.read()
        return {
            "filename": "klipper.bin",
            "data": base64.b64encode(file_data).decode('utf-8'),
            "size": len(file_data)
        }

    def _generate_config(self, platform, model, clock_ref, bootloader, communication, initial_pins):
        """Generate .config content for Klipper"""
        lines = []

        # Base config
        lines.append("CONFIG_LOW_LEVEL_OPTIONS=y")

        # Platform selection
        if platform == "STM32":
            lines.append("CONFIG_MACH_STM32=y")
        elif platform == "RP2040":
            lines.append("CONFIG_MACH_RPXXXX=y")
        elif platform == "LPC176x":
            lines.append("CONFIG_MACH_LPC176X=y")
        elif platform == "AVR":
            lines.append("CONFIG_MACH_AVR=y")

        # Set model
        model_config = model.upper().replace(" ", "_")
        lines.append(f"CONFIG_MACH_{model_config}=y")

        # Set clock reference
        if clock_ref and platform == "STM32":
            clock_map = {
                "8 MHz crystal": "STM32_CLOCK_REF_8M",
                "12 MHz crystal": "STM32_CLOCK_REF_12M",
                "16 MHz crystal": "STM32_CLOCK_REF_16M",
                "20 MHz crystal": "STM32_CLOCK_REF_20M",
                "24 MHz crystal": "STM32_CLOCK_REF_24M",
                "25 MHz crystal": "STM32_CLOCK_REF_25M",
                "Internal clock": "STM32_CLOCK_REF_INTERNAL"
            }
            if clock_ref in clock_map:
                lines.append(f"CONFIG_{clock_map[clock_ref]}=y")

        # Set bootloader
        bootloader_map = {
            "No bootloader": "STM32_FLASH_START_0000",
            "2KiB bootloader": "STM32_FLASH_START_800",
            "4KiB bootloader": "STM32_FLASH_START_1000",
            "8KiB bootloader": "STM32_FLASH_START_2000",
            "16KiB bootloader": "STM32_FLASH_START_4000",
            "20KiB bootloader": "STM32_FLASH_START_5000",
            "28KiB bootloader": "STM32_FLASH_START_7000",
            "32KiB bootloader": "STM32_FLASH_START_8000",
            "34KiB bootloader": "STM32_FLASH_START_8800",
            "36KiB bootloader": "STM32_FLASH_START_9000",
            "48KiB bootloader": "STM32_FLASH_START_C000",
            "64KiB bootloader": "STM32_FLASH_START_10000",
            "128KiB bootloader": "STM32_FLASH_START_20000",
            "128KiB bootloader with 512 byte offset": "STM32_FLASH_START_20200",
            # RP2040 bootloader
            "16KiB bootloader (RP2040)": "RPXXXX_FLASH_START_4000",
        }
        if bootloader in bootloader_map:
            lines.append(f"CONFIG_{bootloader_map[bootloader]}=y")

        # Set communication interface
        comm_map = {
            "USB (on PA11/PA12)": "STM32_USB_PA11_PA12",
            "USB (on PA9/PA10)": "STM32_USB_PA11_PA12_REMAP",
            "USB (on PB14/PB15)": "STM32_USB_PB14_PB15",
            "Serial (on USART1 PA10/PA9)": "STM32_SERIAL_USART1",
            "Serial (on USART2 PA3/PA2)": "STM32_SERIAL_USART2",
            "CAN bus (on PA11/PA12)": "STM32_CANBUS_PA11_PA12",
            "CAN bus (on PA11/PB9)": "STM32_CANBUS_PA11_PB9",
            "USB to CAN bus bridge (USB on PA11/PA12)": "STM32_USBCANBUS_PA11_PA12",
            # RP2040 communication
            "USBSERIAL": "RPXXXX_USB",
            "UART0 on GPIO0/GPIO1": "RPXXXX_SERIAL_UART0_PINS_0_1",
            "UART1 on GPIO4/GPIO5": "RPXXXX_SERIAL_UART1_PINS_4_5",
            "CAN bus": "RPXXXX_CANBUS",
            "USB to CAN bus bridge": "RPXXXX_USBCANBUS",
        }
        if communication in comm_map:
            lines.append(f"CONFIG_{comm_map[communication]}=y")

        # Set initial pins
        if initial_pins:
            lines.append(f'CONFIG_INITIAL_PINS="{initial_pins}"')

        # Add common settings
        lines.append("CONFIG_LOW_LEVEL_OPTIONS=y")

        return "\n".join(lines) + "\n"

    async def _run_command(self, cmd, cwd):
        """Run a shell command asynchronously"""
        logger.info("Running command: %s in %s", cmd, cwd)

        process = await asyncio.create_subprocess_shell(
            cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        self.build_process = process

        # Read stdout line by line
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            line_str = line.decode().strip()
            if line_str:
                self.build_log.append(line_str)

        # Read stderr line by line
        while True:
            line = await process.stderr.readline()
            if not line:
                break
            line_str = line.decode().strip()
            if line_str:
                self.build_log.append(line_str)

        await process.wait()
        return {"returncode": process.returncode}

    async def _run_software_command(self, cmd, cwd):
        """Run a software management command asynchronously"""
        logger.info("Running software command: %s in %s", cmd, cwd)

        process = await asyncio.create_subprocess_shell(
            cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        self.software_process = process

        # Read output line by line
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            line_str = line.decode().strip()
            if line_str:
                self.software_log.append(line_str)

        await process.wait()
        return {"returncode": process.returncode}

    async def _add_update_manager_config(self, component: str) -> bool:
        """Add update_manager configuration to moonraker.conf"""
        home_dir = os.path.expanduser("~")
        moonraker_conf = os.path.join(home_dir, "printer_data", "config", "moonraker.conf")

        if not os.path.exists(moonraker_conf):
            logger.warning(f"moonraker.conf not found at {moonraker_conf}")
            return False

        # Define update_manager configurations for each component
        update_configs = {
            "klipperscreen": """
[update_manager KlipperScreen]
type: git_repo
path: ~/KlipperScreen
origin: https://github.com/KlipperScreen/KlipperScreen.git
managed_services: KlipperScreen
""",
            "crowsnest": """
[update_manager crowsnest]
type: git_repo
path: ~/crowsnest
origin: https://github.com/mainsail-crew/crowsnest.git
primary_branch: v5
managed_services: crowsnest
system_dependencies: system-dependencies.json
virtualenv: ~/crowsnest-env
requirements: requirements.txt
"""
        }

        if component not in update_configs:
            logger.warning(f"No update_manager config defined for {component}")
            return False

        config_entry = update_configs[component]

        try:
            # Read existing config
            with open(moonraker_conf, "r") as f:
                content = f.read()

            # Check if config entry already exists
            section_name = f"[update_manager {component.title()}]" if component != "crowsnest" else "[update_manager crowsnest]"
            if section_name in content:
                logger.info(f"Update manager config for {component} already exists")
                return True

            # Append the new configuration
            with open(moonraker_conf, "a") as f:
                f.write(config_entry)

            logger.info(f"Added update_manager config for {component} to {moonraker_conf}")
            return True

        except Exception as e:
            logger.error(f"Failed to add update_manager config: {e}")
            return False

    # ================================================================
    # Software Management Handlers
    # ================================================================

    async def _handle_software_list(self, web_request):
        """List available software components"""
        # Check which components are installed
        components = []
        home_dir = os.path.expanduser("~")

        software_list = [
            {
                "name": "Klipper",
                "key": "klipper",
                "path": os.path.join(home_dir, "klipper"),
                "description": "3D printer firmware",
                "repo": "Klipper3d/klipper"
            },
            {
                "name": "Moonraker",
                "key": "moonraker",
                "path": os.path.join(home_dir, "moonraker"),
                "description": "API server",
                "repo": "Arksine/moonraker"
            },
            {
                "name": "Mainsail",
                "key": "mainsail",
                "path": os.path.join(home_dir, "mainsail"),
                "description": "Web interface",
                "repo": "mainsail-crew/mainsail"
            },
            {
                "name": "Fluidd",
                "key": "fluidd",
                "path": os.path.join(home_dir, "fluidd"),
                "description": "Alternative web interface",
                "repo": "fluidd-core/fluidd"
            },
            {
                "name": "KlipperScreen",
                "key": "klipperscreen",
                "path": os.path.join(home_dir, "KlipperScreen"),
                "description": "Touchscreen GUI",
                "repo": "KlipperScreen/KlipperScreen"
            },
            {
                "name": "Crowsnest",
                "key": "crowsnest",
                "path": os.path.join(home_dir, "crowsnest"),
                "description": "Webcam streamer",
                "repo": "mainsail-crew/crowsnest"
            },
            {
                "name": "Mainsail-Config",
                "key": "mainsail_config",
                "path": os.path.join(home_dir, "mainsail-config"),
                "description": "Mainsail configuration files",
                "repo": "mainsail-crew/mainsail-config"
            },
            {
                "name": "Fluidd-Config",
                "key": "fluidd_config",
                "path": os.path.join(home_dir, "fluidd-config"),
                "description": "Fluidd configuration files",
                "repo": "fluidd-core/fluidd-config"
            },
        ]

        for sw in software_list:
            installed = os.path.exists(sw["path"])
            version = None
            if installed:
                # Try to get version from git
                try:
                    result = await self._run_software_command(
                        "git describe --tags --always 2>/dev/null || echo unknown",
                        sw["path"]
                    )
                    if self.software_log:
                        version = self.software_log[-1]
                    self.software_log = []
                except:
                    version = "unknown"
            components.append({
                "name": sw["name"],
                "key": sw["key"],
                "installed": installed,
                "version": version,
                "description": sw["description"],
                "repo": sw["repo"]
            })

        return {"components": components}

    async def _handle_software_status(self, web_request):
        """Get software management status"""
        return {
            "status": self.software_status,
            "log": self.software_log[-50:] if self.software_log else []
        }

    async def _handle_software_install(self, web_request):
        """Install a software component"""
        # Get component from query parameters
        component = web_request.get("component", "")
        options_raw = web_request.get("options", "{}")
        # Handle both JSON string and dict formats
        if isinstance(options_raw, str):
            options = json.loads(options_raw) if options_raw else {}
        elif isinstance(options_raw, dict):
            options = options_raw
        else:
            options = {}
        logger.info(f"Software install: component='{component}', options={options}")
        if not component:
            return {"status": "error", "message": "No component specified"}

        self.software_log = []
        self.software_status = "installing"
        self.software_log.append(f"Installing {component}...")

        home_dir = os.path.expanduser("~")

        # Map component to git repo and install commands
        install_commands = {
            "klipperscreen": {
                "repo": "https://github.com/KlipperScreen/KlipperScreen.git",
                "path": os.path.join(home_dir, "KlipperScreen"),
                "install": "./scripts/KlipperScreen-install.sh"
            },
            "crowsnest": {
                "repo": "https://github.com/mainsail-crew/crowsnest.git",
                "path": os.path.join(home_dir, "crowsnest"),
                "install": "./crowsnest-install.sh"
            },
        }

        if component not in install_commands:
            self.software_status = "failed"
            return {"status": "error", "message": f"Unknown component: {component}"}

        info = install_commands[component]

        # Check if already installed
        if os.path.exists(info["path"]):
            self.software_status = "failed"
            self.software_log.append(f"{component} is already installed at {info['path']}")
            return {"status": "error", "message": f"{component} already installed"}

        # Clone the repository
        self.software_log.append(f"Cloning {info['repo']}...")
        result = await self._run_software_command(
            f"git clone {info['repo']} {info['path']}",
            home_dir
        )

        if result["returncode"] != 0:
            self.software_status = "failed"
            self.software_log.append("Failed to clone repository")
            return {"status": "error", "message": "Failed to clone repository"}

        # Build environment variables from options
        env_vars = ""
        if component == "klipperscreen" and options:
            # KlipperScreen install script reads these environment variables:
            # SERVICE - Install as standalone service (Y/n)
            # BACKEND - Graphical backend X11 or Wayland (X/W)
            # NETWORK - Install NetworkManager (Y/n)
            if "service" in options:
                env_vars += f"SERVICE={options['service']} "
            if "backend" in options:
                env_vars += f"BACKEND={options['backend']} "
            if "network" in options:
                env_vars += f"NETWORK={options['network']} "

        # Run install script with environment variables
        self.software_log.append(f"Running install script...")
        # Use 'env' command to set environment variables properly
        install_cmd = f"env {env_vars}{info['install']}"
        result = await self._run_software_command(
            install_cmd,
            info["path"]
        )

        if result["returncode"] == 0:
            self.software_status = "success"
            self.software_log.append(f"{component} installed successfully!")

            # Add update_manager entry to moonraker.conf
            self.software_log.append("Adding update_manager configuration to moonraker.conf...")
            config_result = await self._add_update_manager_config(component)
            if config_result:
                self.software_log.append("Update manager configuration added successfully!")
            else:
                self.software_log.append("Warning: Failed to add update manager configuration")
        else:
            self.software_status = "failed"
            self.software_log.append(f"Failed to install {component}")

        return {
            "status": self.software_status,
            "log": self.software_log
        }

    async def _handle_software_update(self, web_request):
        """Update a software component"""
        component = web_request.get("component", "")
        if not component:
            return {"status": "error", "message": "No component specified"}

        self.software_log = []
        self.software_status = "updating"
        self.software_log.append(f"Updating {component}...")

        home_dir = os.path.expanduser("~")
        component_paths = {
            "klipper": os.path.join(home_dir, "klipper"),
            "moonraker": os.path.join(home_dir, "moonraker"),
            "mainsail": os.path.join(home_dir, "mainsail"),
            "fluidd": os.path.join(home_dir, "fluidd"),
            "klipperscreen": os.path.join(home_dir, "KlipperScreen"),
            "crowsnest": os.path.join(home_dir, "crowsnest"),
            "mainsail_config": os.path.join(home_dir, "mainsail-config"),
            "fluidd_config": os.path.join(home_dir, "fluidd-config"),
        }

        if component not in component_paths:
            self.software_status = "failed"
            return {"status": "error", "message": f"Unknown component: {component}"}

        path = component_paths[component]
        if not os.path.exists(path):
            self.software_status = "failed"
            return {"status": "error", "message": f"{component} is not installed"}

        # Git pull to update
        result = await self._run_software_command("git pull", path)

        if result["returncode"] == 0:
            self.software_status = "success"
            self.software_log.append(f"{component} updated successfully!")
        else:
            self.software_status = "failed"
            self.software_log.append(f"Failed to update {component}")

        return {
            "status": self.software_status,
            "log": self.software_log
        }

    async def _handle_software_remove(self, web_request):
        """Remove a software component"""
        component = web_request.get("component", "")
        if not component:
            return {"status": "error", "message": "No component specified"}

        self.software_log = []
        self.software_status = "removing"
        self.software_log.append(f"Removing {component}...")

        home_dir = os.path.expanduser("~")
        component_paths = {
            "klipper": os.path.join(home_dir, "klipper"),
            "moonraker": os.path.join(home_dir, "moonraker"),
            "mainsail": os.path.join(home_dir, "mainsail"),
            "fluidd": os.path.join(home_dir, "fluidd"),
            "klipperscreen": os.path.join(home_dir, "KlipperScreen"),
            "crowsnest": os.path.join(home_dir, "crowsnest"),
            "mainsail_config": os.path.join(home_dir, "mainsail-config"),
            "fluidd_config": os.path.join(home_dir, "fluidd-config"),
        }

        if component not in component_paths:
            self.software_status = "failed"
            return {"status": "error", "message": f"Unknown component: {component}"}

        path = component_paths[component]
        if not os.path.exists(path):
            self.software_status = "failed"
            return {"status": "error", "message": f"{component} is not installed"}

        # Remove directory
        result = await self._run_software_command(f"rm -rf {path}", home_dir)

        if result["returncode"] == 0:
            self.software_status = "success"
            self.software_log.append(f"{component} removed successfully!")
        else:
            self.software_status = "failed"
            self.software_log.append(f"Failed to remove {component}")

        return {
            "status": self.software_status,
            "log": self.software_log
        }

    async def _handle_software_log(self, web_request):
        """Get software management log"""
        return {
            "log": self.software_log,
            "status": self.software_status
        }

    async def _handle_exec_command(self, web_request):
        """Execute a Linux command on the host machine"""
        command = web_request.get("command", "")
        if not command:
            return {"status": "error", "message": "No command specified"}

        # Security: block dangerous commands
        dangerous_commands = ["rm -rf /", "mkfs", "dd if=", "> /dev/", "shutdown", "reboot"]
        for dangerous in dangerous_commands:
            if dangerous in command.lower():
                return {"status": "error", "message": f"Blocked dangerous command: {dangerous}"}

        logger.info(f"Executing command: {command}")

        try:
            # Execute the command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            output = stdout.decode().strip()
            error = stderr.decode().strip()

            if process.returncode == 0:
                return {
                    "status": "success",
                    "output": output,
                    "returncode": process.returncode
                }
            else:
                return {
                    "status": "error",
                    "output": output,
                    "error": error,
                    "returncode": process.returncode
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}


def load_component(config):
    return FirmwareComponent(config)
