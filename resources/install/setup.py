import os
import subprocess

SERVICE_NAME = "lightbar.service"
SERVICE_PATH = f"/storage/.config/system.d/{SERVICE_NAME}"

SERVICE_CONTENT = """[Unit]
Description=Lightbar Service
DefaultDependencies=no

[Service]
Type=simple
ExecStart=/bin/sh -c \" \\
    modprobe leds_is31fl32xx; \\
    #echo 464 > /sys/class/gpio/export; \\
    #echo out > /sys/class/gpio/gpio464/direction; \\
    #echo 1 > /sys/class/gpio/gpio464/value; \\
    \\
    python /storage/.kodi/addons/service.firecube_lightbar/led.py -a -n 1 -b 100 -f /storage/.kodi/addons/service.firecube_lightbar/resources/animations/ce-anim_start.animation & LED_PID=$!; \\
    while ! systemctl is-active --quiet kodi.service; do sleep 1; done; \\
    sleep 2; \\
    kill $LED_PID; \\
    \\
    python /storage/.kodi/addons/service.firecube_lightbar/led.py -n 1 -b 100 -f /storage/.kodi/addons/service.firecube_lightbar/resources/animations/anim_start_error_short.animation; \\
    \\
    # Turn off all LEDs, enable this if not using a second stop animation \\
    # for i in $(seq 1 15); do \\
    #     echo 0 > /sys/class/leds/led$i/brightness; \\
    # done \\
    \"

[Install]
WantedBy=sysinit.target
"""

SHUTDOWN_SCRIPT = "/storage/.config/shutdown.sh"
SHUTDOWN_LINES = [
    "# Set LED bar red until shutdown is complete",
    "python /storage/.kodi/addons/service.firecube_lightbar/led.py -b 50 -c ff0000"
]

PROFILE_PATH = "/storage/.profile"
ALIAS_LINE = "alias lightbar='python /storage/.kodi/addons/service.firecube_lightbar/led.py'"

def install_service_once():
    if os.path.isfile(SERVICE_PATH):
        return

    try:
        os.makedirs(os.path.dirname(SERVICE_PATH), exist_ok=True)
        with open(SERVICE_PATH, 'w') as f:
            f.write(SERVICE_CONTENT)

        subprocess.run(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "enable", SERVICE_NAME], check=True)

    except Exception as e:
        print(f"Failed to install {SERVICE_NAME}: {e}")

def ensure_shutdown_script():
    try:
        if os.path.exists(SHUTDOWN_SCRIPT):
            with open(SHUTDOWN_SCRIPT, 'r') as f:
                contents = f.read()

            if all(line in contents for line in SHUTDOWN_LINES):
                return  # All lines already present

            with open(SHUTDOWN_SCRIPT, 'a') as f:
                f.write("\n" + "\n".join(SHUTDOWN_LINES) + "\n")

        else:
            with open(SHUTDOWN_SCRIPT, 'w') as f:
                f.write("#!/bin/sh\n\n" + "\n".join(SHUTDOWN_LINES) + "\n")

            os.chmod(SHUTDOWN_SCRIPT, 0o755)

    except Exception as e:
        print(f"Failed to update {SHUTDOWN_SCRIPT}: {e}")

def ensure_lightbar_alias():
    try:
        line = "alias lightbar='python /storage/.kodi/addons/service.firecube_lightbar/led.py'"
        found = False

        if os.path.exists(PROFILE_PATH):
            with open(PROFILE_PATH, "r") as f:
                for l in f:
                    if l.strip().startswith("alias lightbar="):
                        found = True
                        break

        if not found:
            with open(PROFILE_PATH, "a") as f:
                f.write("\n" + line + "\n")
            print("[setup] Appended lightbar alias to .profile")
        else:
            print("[setup] Alias already exists")

    except Exception as e:
        print(f"Failed to ensure lightbar alias: {e}")

def run_setup():
    install_service_once()
    ensure_shutdown_script()
    ensure_lightbar_alias()
