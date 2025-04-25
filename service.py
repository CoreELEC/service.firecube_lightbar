import xbmc
import xbmcaddon
import xbmcgui
import time
from resources.lib.led_controller import LEDMonitor, setup

class LEDService(xbmc.Monitor):
    def __init__(self):
        super(LEDService, self).__init__()
        self.animation_thread = setup()
        self.monitor = LEDMonitor(self.animation_thread)
    
    def run(self):
        while not self.abortRequested():
            if self.monitor.waitForAbort(5):
                if self.animation_thread is not None:
                    self.animation_thread.stop()
                    self.animation_thread.join()
                break

if __name__ == '__main__':
    service = LEDService()
    service.run()
