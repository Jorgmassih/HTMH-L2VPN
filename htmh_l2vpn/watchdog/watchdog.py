from bson import ObjectId

from htmh_l2vpn.access_handler.access_handler import AccessHandler
from htmh_l2vpn.mongodb.mongo_driver import NetworkAnatomy
from htmh_l2vpn.onos.onos import ONOSDriver
from threading import Thread
import time
import logging


class Watchdog:
    def __init__(self):
        self._watch_links = False
        self._watch_hosts = False

        self.access_hd = AccessHandler()


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
        print('Starting watchdog for links...')
        onos_driver = ONOSDriver()
        na = NetworkAnatomy('NetworkStatus')
        na.links = onos_driver.get_links()
        while True:
            links = onos_driver.get_links()
            down_links, restored_links = na.compare_links(links)
            if down_links:
                na.links = links
                logging.warning('{} links are down'.format(str(down_links)))

            if restored_links:
                na.links = links
                logging.warning('{} links was restored'.format(str(restored_links)))

    def __watchdog_hosts(self):
        print('Starting watchdog for hosts...')
        onos_driver = ONOSDriver()
        na = NetworkAnatomy('NetworkStatus')
        na.hosts = onos_driver.get_hosts()
        while True:
            hosts = onos_driver.get_hosts()
            new_hosts = na.new_host(hosts)
            if new_hosts:
                for host in new_hosts:
                    device_id = host.split('-')[1]
                    device_id = ObjectId('0'*8 + device_id)
                    AccessHandler().device_normal_functions(device_id=device_id)
                na.hosts = hosts
                print('New hosts are: ', new_hosts)

    def run(self):
        print("Watchdog has started")
        watchdog_links = Thread(name='Watchdog links', target=self.__watchdog_links)
        watchdog_hosts = Thread(name='Watchdog hosts', target=self.__watchdog_hosts)
        if self.watch_links:
            watchdog_links.start()

        if self.watch_hosts:
            watchdog_hosts.start()
