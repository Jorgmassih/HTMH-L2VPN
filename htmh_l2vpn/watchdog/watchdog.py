from bson import ObjectId

from htmh_l2vpn.access_handler.access_handler import AccessHandler
from htmh_l2vpn.mongodb.mongo_driver import NetworkAnatomy, HTMHService
from htmh_l2vpn.onos.onos import ONOSDriver
from threading import Thread
import time
import logging


class Watchdog:
    def __init__(self):
        self.watch_links = False
        self.watch_hosts = False
        self.watch_services = False


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
                time.sleep(1)
                hosts = onos_driver.get_hosts()
                devices_to_update = na.add_hosts(hosts)
                if devices_to_update:
                    print('here', )
                    for device_to_update in devices_to_update:
                        AccessHandler().device_normal_functions(device_id=device_to_update)

    def __watchdog_services(self):
        print('Starting watchdog for services...')
        services = HTMHService()
        while True:
            time.sleep(0.5)
            pending = services.pending_to_activate
            expired = services.expired
            if pending:
                print('Pending Services: ', pending)

            if expired:
                print('Expired services: ', expired)


    def run(self):
        print("Watchdog has started")
        watchdog_links = Thread(name='Watchdog links', target=self.__watchdog_links)
        watchdog_hosts = Thread(name='Watchdog hosts', target=self.__watchdog_hosts)
        watchdog_services = Thread(name='Watchdog services', target=self.__watchdog_services)
        if self.watch_links:
            watchdog_links.start()

        if self.watch_hosts:
            watchdog_hosts.start()

        if self.watch_services:
            watchdog_services.start()
