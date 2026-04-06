import xbmc, xbmcgui, xbmcvfs
from threading import Thread
from modules.logger import logger

from modules.monitors.ratings import RatingsMonitor
from modules.monitors.image import ImageMonitor, ImageBlur, ImageAnalysisConfig
from modules.databases.ratings import RatingsDatabase
from modules.config import SETTINGS_PATH


class TrailerPlayerMonitor(xbmc.Player):
    def onAVStarted(self):
        if not xbmc.getCondVisibility("Skin.HasSetting(Trailer.AutoSubtitles)"):
            return
        playing_path = xbmc.getInfoLabel("Player.FilenameAndPath")
        nimbus_trailer = xbmc.getInfoLabel("Skin.String(TrailerPlaying)")
        if "slyguy.trailers" not in playing_path and not nimbus_trailer:
            return
        def _enable():
            for _ in range(10):
                streams = self.getAvailableSubtitleStreams()
                if streams:
                    self.setSubtitleStream(0)
                    self.showSubtitles(True)
                    return
                xbmc.sleep(300)
        Thread(target=_enable, daemon=True).start()


class Service(xbmc.Monitor):
    """Main service class that coordinates monitor and rating lookups."""

    def __init__(self):
        super().__init__()
        self._initialize()

    def _initialize(self):
        """Initialize service components."""
        if not xbmcvfs.exists(SETTINGS_PATH):
            xbmcvfs.mkdir(SETTINGS_PATH)

        self.home_window = xbmcgui.Window(10000)
        self.get_infolabel = xbmc.getInfoLabel
        self.get_visibility = xbmc.getCondVisibility
        self.image_monitor = ImageMonitor(ImageBlur, ImageAnalysisConfig())
        self.ratings_monitor = RatingsMonitor(RatingsDatabase(), self.home_window)
        self.trailer_player = TrailerPlayerMonitor()

    def run(self):
        """Start the service and monitor."""
        self.image_monitor.start()
        ratings_thread = None
        while not self.abortRequested():
            if self._should_pause():
                self.waitForAbort(2)
                continue

            if ratings_thread is None or not ratings_thread.is_alive():
                ratings_thread = Thread(
                    target=self.ratings_monitor.process_current_item,
                    daemon=True,
                )
                ratings_thread.start()
            self.waitForAbort(0.2)
        self.image_monitor.stop()

    def _should_pause(self):
        """Determine if service should pause."""
        if self.home_window.getProperty("pause_services") == "true":
            return True

        if xbmc.getSkinDir() != "skin.nimbus":
            return True

        if not self.get_infolabel("Skin.String(mdblist_api_key)"):
            return True

        if not self.get_visibility(
            "Window.IsVisible(videos) | Window.IsVisible(home) | Window.IsVisible(11121) | Window.IsActive(movieinformation) | [[Window.IsVisible(videoosd) | Window.IsVisible(seekbar)] + Skin.HasSetting(Enable.DetailedOSD) + !Skin.HasSetting(Disable.OSDRatings)]"
        ):
            return True

        return False

    def onNotification(self, sender, method, data):
        """Handle Kodi notifications."""
        # logger(
        #     "Notification received - Sender: {}, Method: {}, Data: {}".format(
        #         sender, method, data
        #     ),
        #     1,
        # )
        if sender == "xbmc":
            if method in ("GUI.OnScreensaverActivated", "System.OnSleep"):
                self.home_window.setProperty("pause_services", "true")
            elif method in ("GUI.OnScreensaverDeactivated", "System.OnWake"):
                self.home_window.clearProperty("pause_services")


if __name__ == "__main__":
    service = Service()
    service.run()
