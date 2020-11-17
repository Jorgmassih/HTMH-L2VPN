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

        #self.access_handler = AccessHandler()


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
            time.sleep(1.2)
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

        while True:
                time.sleep(0.5)
                hosts = onos_driver.get_hosts()
                devices_to_update = na.add_hosts(hosts)
                if devices_to_update:
                    print('here', )
                    for device_to_update in devices_to_update:
                        AccessHandler().device_normal_functions(device_id=device_to_update)

    def run(self):
        print("Watchdog has started")
        watchdog_links = Thread(name='Watchdog links', target=self.__watchdog_links)
        watchdog_hosts = Thread(name='Watchdog hosts', target=self.__watchdog_hosts)
        if self.watch_links:
            watchdog_links.start()

        if self.watch_hosts:
            watchdog_hosts.start()
