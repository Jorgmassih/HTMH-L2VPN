import requests
import json
from os import path

import copy


class ONOSDriver:

    def __init__(self):

        config_file = self.__open_config_file(file='config.json')
        api_config = config_file['api']

        self.headers = api_config['headers']
        self.auth = tuple(api_config['auth'])
        self.url = api_config['url']

    @staticmethod
    def __open_config_file(file: str):
        cur_path = path.dirname(__file__)
        new_path = path.relpath('config\\{}'.format(file), cur_path)

        with open(new_path) as json_file:
            config_file = json.load(json_file)

        return config_file

    def get_hosts(self):
        config_file = self.__open_config_file(file='access_sw.json')
        end_points = config_file['endpoints']
        hosts = requests.get(end_points['hosts_info']['get_hosts'].format(self.url),
                             headers=self.headers,
                             auth=self.auth).json()['hosts']

        return hosts

    def get_sw_public_mac(self, id: str):
        config_file = self.__open_config_file(file='access_sw.json')
        end_points = config_file['endpoints']
        device_ports = requests.get(end_points["devices_info"]['get_device_ports'].format(self.url, id),
                                    headers=self.headers,
                                    auth=self.auth).json()['ports']

        mac = '00:ff:00:ff:00:ff'

        for port in device_ports:
            if port['port'] == '1':
                mac = port['annotations']['portMac']
                break

        return mac

    def install_intents(self, macs_pair: tuple):
        config_file = self.__open_config_file(file='access_sw.json')
        end_points = config_file['endpoints']
        intent_flow = config_file['flows']['host2host_intent']
        intent_flow['one'] = macs_pair[0] + '/-1'
        intent_flow['two'] = macs_pair[1] + '/-1'

        response = requests.post(end_points['intents']['post_intent'].format(self.url),
                      headers=self.headers, auth=self.auth, json=intent_flow)

        return response

    def install_arp_flow(self, device_id: str, hosts: dict, ports: list):
        config_file = self.__open_config_file(file='access_sw.json')
        end_points = config_file['endpoints']

        interfaces = []

        macs = list(hosts.keys())

        for mac in macs:
            interface = {
                "name": "{}/{}".format(device_id, mac),
                "ips": [hosts[mac]['ip'] + '/16'],
                "mac": mac.lower()
            }

            interfaces.append(interface)

        flow = {}
        for port in ports:
            location = "{}/{}".format(device_id, port)
            flow.update({location: {"interfaces": interfaces}})

        response = requests.post(end_points['network_config']['ports'].format(self.url),
                                 headers=self.headers, auth=self.auth, json=flow)

        return response

    def install_outgoing_flows(self, device: str, hosts: dict, foreign_hosts: dict, service_token: str):
        config_file = self.__open_config_file(file='access_sw.json')
        end_points = config_file['endpoints']

        flow_list = []

        hosts_macs = list(hosts.keys())
        foreign_macs = list(foreign_hosts.keys())

        for foreign_mac in foreign_macs:
            for host_mac in hosts_macs:
                flow = copy.deepcopy(config_file['flows']['outgoing_traffic'])

                flow['deviceId'] = device
                flow['treatment']['instructions'][0]['mac'] = foreign_hosts[foreign_mac]['public_mac']
                flow['treatment']['instructions'][1]['ip'] = hosts[host_mac]['mapped_ip']

                flow['selector']['criteria'][1]['ip'] = foreign_hosts[foreign_mac]['ip'] + '/32'
                flow['selector']['criteria'][2]['ip'] = hosts[host_mac]['ip'] + '/32'
                flow['selector']['criteria'][3]['mac'] = foreign_mac
                flow_list.append(flow)

        flow = {"flows": flow_list}

        response = requests.post(end_points['flows']['post_flow'].format(self.url, 'l2vpn.outgoing.map.' + service_token),
                                 headers=self.headers, auth=self.auth, json=flow)

        return response

    def install_incoming_flows(self, device: str, hosts: dict, service_token: str):
        config_file = self.__open_config_file(file='access_sw.json')
        end_points = config_file['endpoints']

        flow_list = []

        macs = list(hosts.keys())

        for mac in macs:
            flow = copy.deepcopy(config_file['flows']['incoming_traffic'])

            flow['deviceId'] = device

            flow['treatment']['instructions'][0]['mac'] = mac
            flow['treatment']['instructions'][1]['ip'] = hosts[mac]['ip']

            flow['treatment']['instructions'][2]['port'] = hosts[mac]['port']

            flow['selector']['criteria'][1]['ip'] = hosts[mac]['mapped_ip'] + '/32'

            flow_list.append(flow)

        flows = {"flows": flow_list}

        response = requests.post(end_points['flows']['post_flow'].format(self.url, 'l2vpn.incoming.map.' + service_token),
                                 headers=self.headers, auth=self.auth, json=flows)

        return response

    def install_shortest_path(self, src: str, dst: str, dst_public_mac: str, service_token: str):
        config_file = self.__open_config_file(file='backbone_sw.json')
        end_points = config_file['endpoints']

        src = "%3A".join(src.split(':'))
        dst = "%3A".join(dst.split(':'))

        shortest_path = requests.get(end_points['paths']['get_shortest_path'].format(self.url, src, dst),
                                     headers=self.headers, auth=self.auth).json()

        shortest_path = shortest_path['paths'][0]['links']

        flow_list = []

        for link in shortest_path:
            flow = copy.deepcopy(config_file['flows']['fwd_path'])
            output_port = link['src']['port']
            device_id = link['src']['device']

            flow['deviceId'] = device_id
            flow['treatment']['instructions'][0]['port'] = output_port

            flow['selector']['criteria'][0]['mac'] = dst_public_mac

            flow_list.append(flow)

        flow = {"flows": flow_list}

        response = requests.post(end_points['flows']['post_flow'].format(self.url, 'l2vpn.core.path.' + service_token),
                                 headers=self.headers, auth=self.auth, json=flow)

        return response

    def delete_flow_app(self, app_id: str):
        config_file = self.__open_config_file(file='config.json')
        end_points = config_file['api']['endpoints']
        response = requests.delete(end_points["delete_flows"]["delete_application"][1].format(self.url, app_id),
                                    headers=self.headers,
                                    auth=self.auth)

        return response
