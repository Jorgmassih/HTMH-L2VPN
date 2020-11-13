import re
import string
import ipaddress
from datetime import datetime


class CheckFor:
    @staticmethod
    def mac(mac_value: str):
        validation = re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac_value.lower())
        return True if validation else False

    @staticmethod
    def ip(ip_value: str):
        try:
            ipaddress.ip_address(ip_value)
            return True
        except ValueError:
            return False

    @staticmethod
    def device_id(id: str):
        if 'of:' not in id.lower() or len(id.split(':')) == 1 or len(id.split(':')) > 2:
            return False

        elif len(id.split(':')) == 2 and not all(c in string.hexdigits for c in id.split(':')[1].lower()):
            return False

        else:
            return True


class IpHandler:
    @staticmethod
    def increment_third_octet(ip: str, number_of_times: int = 1):
        result_ip = str(ipaddress.ip_address(ip) + 256 * number_of_times)
        return result_ip


def get_fee(start_datetime: str, end_datetime: str, subscribers_num: str):
    factor = 1.5
    fmt = '%Y-%m-%dT%H:%M'
    d1 = datetime.strptime(start_datetime, fmt)
    d2 = datetime.strptime(end_datetime, fmt)
    minutes = (d2 - d1).total_seconds() / 60.0

    return minutes * factor * int(subscribers_num)

