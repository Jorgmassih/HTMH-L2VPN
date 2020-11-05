from htmh_l2vpn.mongodb.mongo_driver import NetworkAnatomy
from htmh_l2vpn.onos.onos import ONOSDriver
from threading import Thread
import time
import logging


class Watchdog:
    def __init__(self):
        self.na = NetworkAnatomy('NetworkStatus')
        self.onos_driver = ONOSDriver()
        self._watch_links = False
        self._watch_hosts = False
        self.na.links = self.onos_driver.get_links()
        self.na.hosts = self.onos_driver.get_hosts()

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
                self.na.links = links
                logging.warning('{} links are down'.format(str(down_links)))

            if restored_links:
                self.na.links = links
                logging.warning('{} links was restored'.format(str(restored_links)))

    def __watchdog_hosts(self):
        while True:
            hosts = self.onos_driver.get_hosts()
            new_hosts = self.na.new_host(hosts)
            if new_hosts:
                print('New hosts are: ', new_hosts)
                self.na.hosts = hosts

    def run(self):
        print("Watchdog has started")
        watchdog_links = Thread(name='Watchdog links', target=self.__watchdog_links)
        watchdog_hosts = Thread(name='Watchdog hosts', target=self.__watchdog_hosts())
        if self.watch_links:
            watchdog_links.start()

        if self.watch_hosts:
            watchdog_hosts.start()


if __name__ == '__main__':
    w = Watchdog()
    w.watch_hosts = True
    w.run()


