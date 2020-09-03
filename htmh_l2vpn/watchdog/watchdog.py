from htmh_l2vpn.mongodb.mongo_driver import NetworkAnatomy
from htmh_l2vpn.onos.onos import ONOSDriver
from threading import Thread
import time
import warnings

class Watchdog:
    def __init__(self):
        self.na = NetworkAnatomy('NetworkStatus')
        self.onos_driver = ONOSDriver()
        self._watch_links = False
        self._watch_hosts = False

    @property
    def watch_links(self):
        return self._watch_links

    @watch_links.setter
    def watch_links(self, attr: bool):
        self._watch_links = attr

    @property
    def watch_hosts(self):
        return self._watch_hosts

    @watch_hosts.setter
    def watch_hosts(self, attr: bool):
        self._watch_hosts = attr

    def __watchdog_links(self):
        while True:
            links = self.onos_driver.get_links()
            down_links, restored_links = self.na.compare_links(links)
            if down_links:
                warnings.warn('{} links are down'.format(str(down_links)))

            if restored_links:
                warnings.warn('{} links was restored'.format(str(restored_links)))

    def run(self):
        print("Watchdog has started")
        watchdog_links = Thread(name='Watchdog links', target=self.__watchdog_links)
        if self.watch_links:
            watchdog_links.start()

