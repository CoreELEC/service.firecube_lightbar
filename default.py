import xbmc
import xbmcaddon
from resources.lib.led_controller import LEDMonitor, setup

if __name__ == '__main__':
    # Example of manual execution logic
    # This script might trigger certain actions or simply notify that it’s being run manually
    xbmc.log("Running Fire Cube LED Controller manually", xbmc.LOGINFO)
    
    # Initialize LED Controller or perform tasks
    animation_thread = setup()
    monitor = LEDMonitor(animation_thread)
    
    # Run the monitor in a way that it doesn't block Kodi
    while not monitor.abortRequested():
        if monitor.waitForAbort(5):
            if animation_thread is not None:
                animation_thread.stop()
                animation_thread.join()
            break

