import xbmc
import xbmcaddon
import xbmcvfs
import os
import sys
import time
import threading

# Default maximum brightness (255 if not specified)
MAX_BRIGHTNESS = 128

# Define LED paths for RGB channels
LED_PATHS = [
    "/sys/class/leds/led13/brightness", # Red 1st position
    "/sys/class/leds/led14/brightness", # Green 1st position
    "/sys/class/leds/led15/brightness", # Blue 1st position

    "/sys/class/leds/led10/brightness", # Red 2nd position
    "/sys/class/leds/led11/brightness", # Green 2nd position
    "/sys/class/leds/led12/brightness", # Blue 2nd position

    "/sys/class/leds/led7/brightness",  # Red 3rd position
    "/sys/class/leds/led8/brightness",  # Green 3rd position
    "/sys/class/leds/led9/brightness",  # Blue 3rd position

    "/sys/class/leds/led4/brightness",  # Red 4th position
    "/sys/class/leds/led5/brightness",  # Green 4th position
    "/sys/class/leds/led6/brightness",  # Blue 4th position
            
    "/sys/class/leds/led1/brightness",  # Red 5th position
    "/sys/class/leds/led2/brightness",  # Green 5th position
    "/sys/class/leds/led3/brightness",  # Blue 5th position
]

class LEDMonitor(xbmc.Monitor):
    def __init__(self, thread=None):
        super().__init__()
        self.effect_thread = thread

    def onSettingsChanged(self):
        if self.effect_thread is not None:
            self.effect_thread.stop()
            self.effect_thread.join()
            self.effect_thread = None

        self.effect_thread = setup()

def read_frames_from_file(file_path):
    """Read animation frames from a file, ignoring lines that start with 'loop', '#' or are blank"""
    if not os.path.exists(file_path):
        print(f"File path {file_path} does not exist", file=sys.stderr)
        sys.exit(1)
    with open(file_path, 'r') as f:
        lines = f.read().splitlines()
    # Ignore lines that start with 'loop', '#' or are blank
    frames = [line for line in lines if line.strip() and not (line.strip().lower().startswith('loop') or line.strip().startswith('#'))]
    return frames

def convert_hex_to_rgb(hex_value):
    """Convert 3 or 6-character hex value to RGB brightness values"""
    if len(hex_value) == 3:
        # Convert 3-character hex to 6-character hex
        hex_value = ''.join([c*2 for c in hex_value])
    elif len(hex_value) == 6:
        # No conversion needed for 6-character hex
        pass
    else:
        raise ValueError(f"Invalid hex value length: {hex_value}")
    
    try:
        red = int(hex_value[0:2], 16)
        green = int(hex_value[2:4], 16)
        blue = int(hex_value[4:6], 16)
    except ValueError as e:
        raise ValueError(f"Error converting hex value to RGB: {hex_value} - {e}")

    # Scale values to MAX_BRIGHTNESS
    red = int(red * MAX_BRIGHTNESS / 255)
    green = int(green * MAX_BRIGHTNESS / 255)
    blue = int(blue * MAX_BRIGHTNESS / 255)
    
    return red, green, blue

def set_brightness(led_file_handles, frame, delay, stop_event):
    """Set the brightness for all LEDs and apply delay"""
    hex_values = frame.split(',')
    for i in range(min(len(hex_values), len(LED_PATHS) // 3)):
        hex_value = hex_values[i]
        if len(hex_value) not in {3, 6}:
            continue
        
        try:
            red, green, blue = convert_hex_to_rgb(hex_value)
        except ValueError:
            continue

        led_file_handles[i * 3].write(f"{red}\n")
        led_file_handles[i * 3 + 1].write(f"{green}\n")
        led_file_handles[i * 3 + 2].write(f"{blue}\n")

    # Flush the file handles to ensure the values are written
    for handle in led_file_handles:
        handle.flush()

    # Use the full delay in seconds
    delay_seconds = delay / 1000.0
    end_time = time.time() + delay_seconds
    while time.time() < end_time:
        if stop_event.is_set():
            break
        time.sleep(0.01)  # Check for stop event every 10ms to stay responsive

def run_animation(animation_file, brightness, stop_event):
    frames = read_frames_from_file(animation_file)
    global MAX_BRIGHTNESS
    MAX_BRIGHTNESS = int((brightness / 100.0) * 255)

    # Open LED paths once and keep the file handles open
    led_file_handles = []
    for path in LED_PATHS:
        try:
            handle = open(path, 'w')
            led_file_handles.append(handle)
        except IOError as e:
            print(f"Error opening {path}: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        while not stop_event.is_set():
            for frame_line in frames:
                if stop_event.is_set():
                    break
                delay_str, frame = frame_line.split(':', 1)
                try:
                    delay = int(delay_str)
                except ValueError:
                    continue

                set_brightness(led_file_handles, frame, delay, stop_event)
    finally:
        # Turn off all LEDs and close file handles
        for handle in led_file_handles:
            try:
                handle.write("0\n")
                handle.flush()
                handle.close()
            except IOError as e:
                print(f"Error turning off LEDs: {e}", file=sys.stderr)
                sys.exit(1)

class AnimationThread(threading.Thread):
    def __init__(self, animation_file, brightness):
        super().__init__()
        self.animation_file = animation_file
        self.brightness = brightness
        self.stop_event = threading.Event()

    def run(self):
        run_animation(self.animation_file, self.brightness, self.stop_event)

    def stop(self):
        self.stop_event.set()

def hex_to_rgb(hex_color):
    # Remove any leading '#' character
    hex_color = hex_color.lstrip('#')
    # Convert hex to RGB
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def set_led_color(red, green, blue, brightness):
    # Map the brightness percentage to 0-255 range
    brightness = int((brightness / 100.0) * 255)
    red = int((red / 255.0) * brightness)
    green = int((green / 255.0) * brightness)
    blue = int((blue / 255.0) * brightness)
    
    # Apply color and brightness to LEDs
    for i in range(1, 16, 3):
        with open(f'/sys/class/leds/led{i}/brightness', 'w') as f:
            f.write(str(red))
        with open(f'/sys/class/leds/led{i+1}/brightness', 'w') as f:
            f.write(str(green))
        with open(f'/sys/class/leds/led{i+2}/brightness', 'w') as f:
            f.write(str(blue))

def setup():
    addon = xbmcaddon.Addon(id='service.firecube_lightbar')
    
    # Retrieve settings
    enable_led_controller = addon.getSetting('enable_led_controller') == 'false'
    color_name = addon.getSetting('color_name')
    hex_color = addon.getSetting('color')
    brightness = int(addon.getSetting('brightness'))  # Combined brightness slider value
    enable_animation = addon.getSetting('enable_animation') == 'true'
    animation_file = xbmcvfs.translatePath(addon.getSetting('animation'))

    if enable_led_controller:
        # Set all LEDs to off (black) if the LED controller is enabled
        set_led_color(0, 0, 0, 100)
        return None

    if enable_animation and animation_file:
        animation_thread = AnimationThread(animation_file, brightness)
        animation_thread.start()
        return animation_thread
    else:
        if color_name == 'hex color code':
            # Use hex color code as provided, handle missing '#'
            hex_color = hex_color.lstrip('#') if hex_color else 'FFFFFF'
            hex_color = f'#{hex_color}'
            try:
                rgb_color = hex_to_rgb(hex_color)
            except ValueError:
                # If hex color conversion fails, default to white
                rgb_color = (255, 255, 255)
        else:
            # Use predefined color names
            color_map = {
                'white': '#FFFFFF',
                'red': '#FF0000',
                'orange': '#FF3300',
                'yellow': '#FFFF00',
                'light green': '#33FF00',
                'green': '#00FF00',
                'cyan': '#00FF33',
                'light blue': '#00FFFF',
                'blue': '#0066FF',
                'dark blue': '#0000FF',
                'indigo': '#3300FF',
                'purple': '#FF00FF',
                'magenta': '#FF0033'
            }
            hex_color = color_map.get(color_name, '#FFFFFF')
            try:
                rgb_color = hex_to_rgb(hex_color)
            except ValueError:
                # If color mapping or conversion fails, default to white
                rgb_color = (255, 255, 255)

        red, green, blue = rgb_color
        set_led_color(red, green, blue, brightness)
        return None


# Start the main loop
if __name__ == "__main__":
    monitor = LEDMonitor()
    animation_thread = setup()
    try:
        while not monitor.waitForAbort(1):
            pass
    finally:
        if animation_thread:
            animation_thread.stop()
            animation_thread.join()

