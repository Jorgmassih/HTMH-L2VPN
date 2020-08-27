import itertools
import copy
import warnings
from htmh_l2vpn.utils.utils import CheckFor, IpHandler
import logging


class AccessSw:
    def __init__(self, id: str, public_mac: str):
        if not CheckFor().device_id(id=id):
            warnings.warn(message="Invalid device ID '{}'. Many functions couldn't work for this host.".format(id),
                          category=ImportWarning)

        if not CheckFor().mac(mac_value=public_mac):
            warnings.warn(message="Invalid MAC Address: {}. Many functions couldn't work for this host.".format(public_mac),
                          category=ImportWarning)

        self.device_id = id.lower()
        self.public_mac = public_mac.lower()
        self.hosts = {}
        self.foreign_hosts = {}

    def __repr__(self):
        return self.device_id

    def __len__(self):
        return len(self.hosts)

    @property
    def pairs_mac(self):
        if len(self.hosts) > 1:
            macs_list = list(self.hosts.keys())
            pairs = itertools.combinations(macs_list, 2)
            return pairs

        return None

    @property
    def all_hosts(self):
        if self.hosts or self.foreign_hosts:
            new_dict = copy.deepcopy(self.hosts)
            new_dict.update(self.foreign_hosts)
            return new_dict

        return None

    @property
    def active_ports(self):
        if self.hosts:
            ports = [self.hosts[host]['port'] for host in self.hosts.keys()]
            return ports

        return None

    def add_host(self, mac: str, ip: str, port: int):
        # Check for non-legit MAC format
        if not CheckFor().mac(mac_value=mac):
            logging.warning('MAC value is not legit for host ({},{},{}). It wont be added'.format(mac, ip, port))

        elif not CheckFor().ip(ip_value=ip):
            logging.warning('Ip value is not legit for host ({},{},{}). It wont be added'.format(mac, ip, port))

        else:
            self.hosts.update({mac.lower(): {'ip': ip, 'port': port}})

    def add_foreign_hosts(self, src_device_mac: str, hosts: dict):
        if not CheckFor().mac(src_device_mac):
            logging.warning('Public MAC {} is not valid MAC. It wont be added.')

        else:
            for host in list(hosts.keys()):
                self.foreign_hosts.update({host.lower(): {'ip': hosts[host]['mapped_ip'],
                                                          'public_mac': src_device_mac.lower()}})

    def map_ips(self, range_id: int):
        print('\n===== Mapping Ips for {} ====='.format(self.device_id))
        mapped_ips = []
        for mac in self.hosts.keys():
            host_info = self.hosts[mac]
            ip = host_info['ip']
            ip_to_map = IpHandler.increment_third_octet(ip=ip, number_of_times=range_id)
            host_info.update({'mapped_ip': ip_to_map})
            self.hosts.update({mac: host_info})
            print('{} was mapped to {}'.format(self.hosts[mac]['ip'], self.hosts[mac]['mapped_ip']))
            mapped_ips.append(ip_to_map)

        return mapped_ips

    def wipe_hosts(self):
        self.hosts = {}

    def wipe_foreign_hosts(self):
        self.foreign_hosts = {}
