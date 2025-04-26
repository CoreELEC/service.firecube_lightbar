import xbmc
import xbmcaddon
import xbmcgui
from resources.lib.led_controller import LEDMonitor, setup

# Optional one-time setup hook
try:
    from resources.install.setup import (
        install_service_once,
        ensure_shutdown_script,
        ensure_lightbar_alias
    )
    install_service_once()
    ensure_shutdown_script()
    ensure_lightbar_alias()
except Exception as e:
    xbmc.log(f"[lightbar setup error] {e}", xbmc.LOGERROR)


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

