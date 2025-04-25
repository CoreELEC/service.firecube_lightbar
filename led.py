#!/usr/bin/env python3

import argparse
import os
import sys
import time

# Default maximum brightness (255 if not specified)
MAX_BRIGHTNESS = 255

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

class CustomHelpFormatter(argparse.HelpFormatter):
    def _get_default_metavar_for_optional(self, action):
        return ''

    def _format_action_invocation(self, action):
        if action.dest == 'brightness':
            return '-b, --brightness'
        elif action.dest == 'file':
            return '-f, --file'
        elif action.dest == 'color':
            return '-c, --color'
        elif action.dest == 'time':
            return '-t, --time'
        elif action.dest == 'number':
            return '-n, --number'
        elif action.dest == 'infinity':
            return '-i, --infinity'
        elif action.dest == 'animate':
            return '-a, --animate'
        else:
            return super()._format_action_invocation(action)

def main():
    parser = argparse.ArgumentParser(
        description='Fire Cube LED controller',
        formatter_class=CustomHelpFormatter
    )
    parser.add_argument('-b', '--brightness', type=int, default=128, help='Set brightness')
    
    # Define mutually exclusive group for animation and solid color options
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', type=str, help='Path to file with frame data')
    group.add_argument('-c', '--color', type=str, help='Set a solid color for all LEDs')
    
    # Define mutually exclusive group for timing options
    time_group = parser.add_mutually_exclusive_group()
    time_group.add_argument('-t', '--time', type=int, help='Loop time in seconds')
    time_group.add_argument('-n', '--number', type=int, help='Number of times to loop the animation')
    time_group.add_argument('-i','--infinity', action='store_true', help='Loop the animation indefinitely')

    parser.add_argument('-a', '--animate', action='store_true', help='Use in file loop instructions')
    
    args = parser.parse_args()
    global MAX_BRIGHTNESS
    MAX_BRIGHTNESS = args.brightness

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
        if args.color:
            # Set a solid color
            set_solid_color(led_file_handles, args.color)
            # Do not turn off LEDs; leave them on indefinitely
            sys.exit(0)
        elif args.file:
            # Read frames from file
            frames = read_frames_from_file(args.file, args.animate)
            if args.time:
                # Run animation for a specified loop time
                end_time = time.time() + args.time
                current_time = time.time()
                while current_time < end_time:
                    for frame_line in frames:
                        delay_str, frame = frame_line.split(':', 1)
                        try:
                            delay = int(delay_str)
                        except ValueError:
                            continue

                        set_brightness(led_file_handles, frame, delay)
                        current_time = time.time()
                        if current_time >= end_time:
                            break
            elif args.number:
                # Loop the animation a specified number of times
                for _ in range(args.number):
                    for frame_line in frames:
                        delay_str, frame = frame_line.split(':', 1)
                        try:
                            delay = int(delay_str)
                        except ValueError:
                            continue

                        set_brightness(led_file_handles, frame, delay)
            elif args.infinity:
                # Loop the animation indefinitely
                while True:
                    for frame_line in frames:
                        delay_str, frame = frame_line.split(':', 1)
                        try:
                            delay = int(delay_str)
                        except ValueError:
                            continue

                        set_brightness(led_file_handles, frame, delay)
    finally:
        # Turn off all LEDs and close file handles if not in color mode
        if not args.color:
            for handle in led_file_handles:
                try:
                    handle.write("0\n")
                    handle.flush()
                    handle.close()
                except IOError as e:
                    print(f"Error turning off LEDs: {e}", file=sys.stderr)
                    sys.exit(1)

def read_frames_from_file(file_path, use_animate=False):
    """Read animation frames from a file, ignoring lines that start with 'loop', '#', or are blank unless -a is used"""
    if not os.path.exists(file_path):
        print(f"File path {file_path} does not exist", file=sys.stderr)
        sys.exit(1)
    with open(file_path, 'r') as f:
        lines = f.read().splitlines()

    if not use_animate:
        # Ignore lines that start with 'loop', '#' or are blank
        frames = [line for line in lines if line.strip() and not (line.strip().lower().startswith('loop') or line.strip().startswith('#'))]
    else:
        frames = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.lower().startswith('loop'):
                try:
                    loop_count = int(line.split()[1])
                except (IndexError, ValueError):
                    i += 1
                    continue
                loop_start = i + 1
                loop_end = loop_start
                while loop_end < len(lines) and lines[loop_end].strip():
                    loop_end += 1
                loop_lines = lines[loop_start:loop_end]
                for _ in range(loop_count):
                    frames.extend(loop_lines)
                i = loop_end
            elif line and not line.startswith('#'):
                frames.append(line)
            i += 1

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

def set_brightness(led_file_handles, frame, delay):
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

    time.sleep(delay / 1000.0)  # Convert milliseconds to seconds

def set_solid_color(led_file_handles, color):
    """Set a solid color for all LEDs"""
    try:
        red, green, blue = convert_hex_to_rgb(color)
    except ValueError:
        print(f"Invalid color value: {color}", file=sys.stderr)
        sys.exit(1)

    for i in range(len(LED_PATHS)):
        if i % 3 == 0:
            led_file_handles[i].write(f"{red}\n")
        elif i % 3 == 1:
            led_file_handles[i].write(f"{green}\n")
        elif i % 3 == 2:
            led_file_handles[i].write(f"{blue}\n")

    # Flush the file handles to ensure the values are written
    for handle in led_file_handles:
        handle.flush()

if __name__ == "__main__":
    main()

