import copy
import itertools

from pymongo import MongoClient
from bson.objectid import ObjectId
from random_object_id import generate
import datetime

from htmh_l2vpn.utils.utils import IpHandler


class MongoDriver:
    def __init__(self, db_name: str):
        self.db_name = db_name

    @property
    def db(self):
        with MongoClient(self.mongo_uri) as client:
            db_ = client[self.db_name]
        return db_

    @property
    def mongo_uri(self):
        #mongo_uri = "mongodb+srv://jorgmassih:Jamv1420290@htmh-db.ll4nf.gcp.mongodb.net/{}?retryWrites=true&w=majority".format(self.db_name)
        mongo_uri = "mongodb://127.0.0.1:27017".format(self.db_name)
        return mongo_uri


class GetConfig(MongoDriver):
    def __init__(self, db_name: str, collection: str = '', doc: str = ''):
        super().__init__(db_name)
        self._collection_ = collection
        self.data_key = 'data'
        self.doc = doc

    @property
    def collection(self):
        if self._collection_ not in self.db.list_collection_names():
            raise Exception('Invalid collection')
        return self.db[self._collection_]

    @collection.setter
    def collection(self, attr):
        self._collection_ = attr

    def __getattr__(self, attr):
        if not self.doc:
            raise Exception('You must set doc attribute first')

        coll = self.collection.find_one({'type': self.doc})
        data = coll[self.data_key]
        if attr in data:
            return data[attr]
        else:
            raise Exception('Invalid key')


class NetworkAnatomy(MongoDriver):
    def __init__(self, db_name: str = 'NetworkStatus'):
        MongoDriver.__init__(self, db_name)

    @property
    def hosts(self):
        collection = self.db['AnatomyHosts']
        collection.create_index([('deviceId', 1)])
        hosts_ = list(collection.find())
        return hosts_

    @staticmethod
    def convert_host_format(host: dict):
        device_id, port, friendly_name, ip = ObjectId('0'*8 + host['locations'][0]['elementId'][3:]),\
                                             host['locations'][0]['port'], host['mac'], host['ipAddresses'][0]
        host['deviceId'], host['port'], host['friendlyName'], host['ip'], host['virtualIp'] = \
            device_id, port, friendly_name, ip, ''

        host.pop('id')
        host.pop('locations')
        host.pop('ipAddresses')

        return host

    def get_host_public_mac(self, device_id: ObjectId):
        collection = self.db['AnatomyAccessDevices']
        device = collection.find_one({'_id': device_id})
        public_mac = device['publicMac']
        return public_mac

    def _get_host_id(self, host: dict):
        if not host.get('deviceId'):
            host = self.convert_host_format(host)

        mac = host['mac']
        device_id = str(host['deviceId'])[8:]
        return '{}-{}'.format(mac, device_id)

    def add_hosts(self, hosts: list):
        hosts_ids = None
        if hosts:
            collection = self.db['AnatomyHosts']
            new_hosts = self.new_host(hosts)

            if new_hosts:
                hosts_to_insert = []

                for host in hosts:
                    if '{}-{}'.format(host['mac'], str(host['deviceId'])[8:]) not in new_hosts:
                        continue

                    host['publicMac'] = self.get_host_public_mac(host['deviceId'])
                    hosts_to_insert.append(host)

                collection.insert_many(hosts_to_insert)

                hosts_ids = [ObjectId('0'*8 + host_id.split('-')[1]) for host_id in new_hosts]
                print('New hosts are: ', new_hosts)
                hosts_ids = set(hosts_ids)

        return hosts_ids

    @property
    def hosts_ids(self):
        ids = set(map(self._get_host_id, self.hosts))
        return ids

    @property
    def access_devices(self):
        collection = self.db['AnatomyAccessDevices']
        devices = list(collection.find())
        return devices

    @property
    def access_devices_ids(self):
        devices = self.access_devices
        devices = [device['_id'] for device in devices]
        return devices

    @property
    def core_devices(self):
        collection = self.db['AnatomyCoreDevices']
        devices = list(collection.find())
        return devices

    @property
    def links(self):
        collection = self.db['AnatomyLinks']
        links_ = list(collection.find())
        return links_

    @links.setter
    def links(self, new_links: list):
        if new_links:
            collection = self.db['AnatomyLinks']
            collection.delete_many({})
            for link in new_links:

                link_id = '{}-{}-{}-{}'.format(link['src']['device'], link['src']['port'],
                                               link['dst']['device'], link['dst']['port'])
                link['_id'] = link_id
            collection.insert_many(new_links)

    @property
    def links_ids(self):
        ids = set()
        for link in self.links:
            ids.add(link['_id'])

        return ids

    def insert_link(self, link: dict):
        collection = self.db['AnatomyLinks']
        link_id = '{}-{}-{}-{}'.format(link['src']['device'], link['src']['port'],
                                       link['dst']['device'], link['dst']['port'])
        link['_id'] = link_id
        collection.insert_one(link)

    def new_host(self, hosts: list):
        ids_to_compare = set(map(self._get_host_id, hosts))
        return ids_to_compare - self.hosts_ids

    def compare_links(self, links_to_compare: list):
        ids_to_compare = set()
        for link in links_to_compare:
            link_id = '{}-{}-{}-{}'.format(link['src']['device'], link['src']['port'],
                                           link['dst']['device'], link['dst']['port'])
            ids_to_compare.add(link_id)

        return self.links_ids - ids_to_compare, ids_to_compare - self.links_ids


class HTMHDevice(MongoDriver):

    class DeviceIdentifier(MongoDriver):
        def __init__(self, device_id: ObjectId):
            MongoDriver.__init__(self, db_name='Services')
            self.collection = self.db['Htmh']
            self.device_id = device_id

        def devices_in_same_service(self):
            query = {'isUsable': True, 'subscribers': {'$elemMatch': {'equipment': self.device_id}}}
            devices = self.collection.find_one(query)['subscribers']
            devices = [device['equipment'] for device in devices if device['equipment'] != self.device_id
                       and device['active']]
            return devices

    def __init__(self, device_id, is_foreign: bool = False):
        MongoDriver.__init__(self, db_name='NetworkStatus')
        self.is_foreign = is_foreign

        if type(device_id) is str:
            self.device_id = ObjectId('0'*8 + device_id.lower()[3:])

        elif type(device_id) is ObjectId:
            self.device_id = device_id

    @property
    def of_id(self):
        of_id = 'of:' + str(self.device_id)[8:]
        return of_id

    @property
    def hosts(self):
        collection = self.db['AnatomyHosts']
        query = {'deviceId': self.device_id}
        hosts = []
        if self.is_foreign:
            for host in collection.find(query):
                host['ip'] = host['virtualIp']
                hosts.append(host)
            return hosts

        hosts = [host for host in collection.find(query)]
        return hosts

    @hosts.setter
    def hosts(self, new_hosts):
        collection = self.db['AnatomyHosts']

        collection.delete_many({'deviceId': self.device_id})
        collection.insert_many(new_hosts)

    @property
    def foreign_hosts(self):
        devices_id = self.DeviceIdentifier(device_id=self.device_id).devices_in_same_service()
        hosts = [HTMHDevice(device_id=device_id, is_foreign=True).hosts for device_id in devices_id]
        hosts = list(itertools.chain(*hosts))

        return hosts

    @property
    def pairs_mac(self):
        if len(self.hosts) > 1:
            macs_list = [host['mac'] for host in self.hosts]
            pairs = itertools.combinations(macs_list, 2)
            return pairs

        return None

    @property
    def all_hosts(self):
        hosts = self.hosts
        foreign = self.foreign_hosts
        if hosts or foreign:
            all_hosts = [*hosts, *foreign]
            return all_hosts

        return None

    @property
    def active_ports(self):
        if self.hosts:
            ports = [host['port'] for host in self.hosts]
            return ports

        return None

    @property
    def public_mac(self):
        collection = self.db['AnatomyAccessDevices']
        public_mac = collection.find_one({'_id': self.device_id})
        public_mac = public_mac['publicMac']
        return public_mac

    def maps_ip(self, range_id):
        hosts = self.hosts
        for host in hosts:
            ip = host['ip']
            ip_to_map = IpHandler.increment_third_octet(ip=ip, number_of_times=range_id)
            host['virtualIp'] = ip_to_map

        self.hosts = hosts

    def reset_virtual_ips(self):
        collection = self.db['AnatomyHosts']
        query = {'deviceId': self.device_id}
        collection.update_many(query, {'$set': {'virtualIp': ''}})


class UserNetworkAnatomy(MongoDriver):
    def __init__(self, user_id: str):
        MongoDriver.__init__(self, db_name='NetworkStatus')
        self.device_id = User(user_id=user_id).equipment_id

    def get_devices_list(self):
        collection = self.db['AnatomyHosts']
        collection.create_index([('deviceId', 1)])
        query = {'deviceId': self.device_id}
        hosts = []
        keys_to_filter = ['mac', 'ip', 'virtualIp', 'friendlyName']
        for host in collection.find(query):
            filtered = dict((k, host[k]) for k in keys_to_filter if k in host)
            hosts.append(filtered)

        return hosts

    def change_friendly_name(self, mac: str, new_friendly_name: str):
        collection = self.db['AnatomyHosts']
        collection.create_index([('deviceId', 1)])
        query = {'mac': mac, 'deviceId': self.device_id}
        update = collection.find_one_and_update(filter=query, update={'$set': {'friendlyName': new_friendly_name}},
                                                upsert=False, return_document=True)

        return True if update else False


class User(MongoDriver):
    def __init__(self, user_id):
        MongoDriver.__init__(self, db_name='UserInfo')
        self.collection = self.db['User']
        if type(user_id) == str:
            self.user = ObjectId('0'*13 + user_id)
        else:
            self.user = user_id
        self.collection.create_index([('token', 1), ('actualService', 1), ('equipmentId', 1)])

    @property
    def user_str(self):
        user = str(self.user)[-11:]
        return user

    def is_logged(self):
        query = {"documentId": self.user, "webApp.logged": True}

        return True if self.collection.find_one(query) else False

    def login(self, password):
        query = {"documentId": self.user, "webApp.logged": False, "webApp.password": password}
        update = self.collection.find_one_and_update(filter=query, update={'$set': {'webApp.logged': True}},
                                                     upsert=False, return_document=True)
        if not update:
            print('Entry not found at login')
            return False

        return True

    def logout(self):
        query = {"documentId": self.user, "webApp.logged": True}
        update = self.collection.find_one_and_update(filter=query, update={'$set': {'webApp.logged': False}},
                                                     upsert=False, return_document=True)
        if not update:
            print('Entry not found at login')
            return False
        return True

    @property
    def actual_service(self):
        query = {"documentId": self.user}
        actual_service = self.collection.find_one(filter=query)
        actual_service = actual_service['actualService']

        return actual_service

    @actual_service.setter
    def actual_service(self, param):
        query = {'documentId': self.user}
        self.collection.update_one(query, {'$set': {'actualService': param}})


    @property
    def first_name(self):
        query = {"documentId": self.user}
        first_name = self.collection.find_one(filter=query)['firstName']
        return first_name

    @property
    def equipment_id(self):
        query = {"documentId": self.user}
        device = self.collection.find_one(filter=query)['equipmentId']
        return device

    @property
    def fullname(self):
        query = {"documentId": self.user}
        user = self.collection.find_one(filter=query)
        first_name = user['firstName']
        last_name = user['lastName']

        return first_name + ' ' + last_name


class Services(MongoDriver):
    def __init__(self, user_id):
        self.user = User(user_id=user_id)

        MongoDriver.__init__(self, db_name='Services')
        self.collection = self.db['Htmh']
        self.collection.create_index([('token', 1)])

    @property
    def htmh_subscribers(self):
        service = self.collection.find_one({'token': self.user.actual_service})
        response = None
        subscribers_list = []

        if not service:
            response = 'This user is not subscribed to any service'
            return {'response': response, 'subs_list': subscribers_list}

        user_id = self.user.user

        subscribers_list = [{'userId': str(subscriber['userId'])[-11:],
                             'name': subscriber['name'],
                             'equipment': str(subscriber['equipment'])[-16:],
                             'active': subscriber['active']}
                            for subscriber in service['subscribers'] if subscriber['userId'] != user_id]

        return {'response': response, 'subs_list': subscribers_list}

    @property
    def is_running(self):
        service = self.collection.find_one({'token': self.user.actual_service})
        return service['isRunning']

    @property
    def htmh_devices(self):
        service = self.collection.find_one({'token': self.user.actual_service})
        response = None

        if not service:
            response = 'This user is not subscribed to any service'
            return {'response': response, 'subs_list': []}

        devices_list = [subscriber['equipment'] for subscriber in service['subscribers'] if subscriber['active']]
        return {'response': response, 'subs_list': devices_list}

    def create_one(self, content):
        response = {'serviceToken': None, 'message': None}

        content['subscribers'] = []
        content['isRunning'] = False
        content['isUsable'] = True
        content['permitRun'] = False
        content['subscribersNum'] = int(content['subscribersNum'])
        content['startDatetime'] = datetime.datetime.strptime(content['startDatetime'] + ':0.00z',
                                                              "%Y-%m-%dT%H:%M:%S.%fz")
        content['endDatetime'] = datetime.datetime.strptime(content['endDatetime'] + ':0.00z',
                                                            "%Y-%m-%dT%H:%M:%S.%fz")

        if content['startDatetime'] > content['endDatetime']:
            response['message'] = 'Invalid dates'
            return response

        if content['startDatetime'] < datetime.datetime.now():
            response['message'] = 'Services cannot exist in the past'
            return response

        if (content['endDatetime'] - content['startDatetime']).total_seconds()/60 < 5:
            response['message'] = 'Service minimum time is 30 minutes'
            return response

        service_token = ObjectId(generate())
        content['token'] = service_token

        if not self.user.actual_service:
            self.user.actual_service = service_token
            content['subscribers'].append({'name': self.user.fullname,
                                           'equipment': self.user.equipment_id,
                                           'userId': self.user.user,
                                           'active': True})
        else:
            response['message'] = 'The User is already on another service'
            return response

        inserting = self.collection.insert_one(content).inserted_id
        response['message'] = 'success'
        response['serviceToken'] = str(content['token'])
        return response

    def add_user_to(self, content):
        response = None

        token = ObjectId(content['serviceToken'])
        secret_key = content['secretKey']
        service = self.collection.find_one({'token': token})

        if not service:
            response = 'Invalid Token'
            return response

        if not service['isUsable']:
            response = 'Service already deleted'
            return response

        if self.user.actual_service:
            response = 'User is already on a service'
            return response

        if not (len(service['subscribers']) <= service['subscribersNum']):
            response = 'Service is full'
            return response

        if service['secretKey'] != secret_key:
            response = 'Invalid key'
            return response

        service['subscribers'].append({'name': self.user.fullname,
                                       'equipment': self.user.equipment_id,
                                       'userId': self.user.user,
                                       'active': True})

        new_values = {"$set": service}

        self.user.actual_service = token

        self.collection.update_one({'token': token}, new_values)

        return response

    def kill_one(self):
        service_token = self.user.actual_service
        response = {'message': None}

        if service_token is None:
            response['message'] = 'Service not found'
            return response
        service = self.collection.find_one({'token': service_token})

        if service is None or not service['isUsable']:
            response['message'] = 'Service not existing'
            return response

        user_id = self.user.user
        if service['subscribers'][0]['userId'] != user_id:
            user_device = self.user.equipment_id
            user_fullname = self.user.fullname
            user_active_status = True

            user_object = {'name': user_fullname, 'equipment': user_device, 'userId': user_id,
                           'active': user_active_status}

            idx = service['subscribers'].index(user_object)
            self.collection.update_one({'token': service_token},
                                       {'$set': {'subscribers.{}.active'.format(idx): False},
                                        '$inc': {'subscribersNum': -1}})

            self.user.actual_service = None
            response['one_subscriber'] = True
            response['message'] = 'success'
            return response

        self.collection.update_one({'token': service_token}, {'$set':
                                                                     {"permitRun": False,
                                                                      'isRunning': False,
                                                                      'isUsable': False}})
        for subscriber in service['subscribers']:
            User(subscriber['userId']).actual_service = None

        response['message'] = 'success'
        return response

    def show_one(self):
        response = {'message': None, 'content': None}

        user_actual_service = self.user.actual_service
        if user_actual_service is None:
            response['message'] = 'Service not found'
            return response

        service_info = self.collection.find_one({'token': user_actual_service})
        if service_info is None or not service_info['isUsable']:
            response['message'] = 'Service not existing'
            return response

        result_service = dict()

        result_service['serviceToken'] = str(service_info['token'])

        result_service['subscribersList'] = [{'name': subscriber['name'],
                                              'equipment': str(subscriber['equipment'])[-16:],
                                              'active': subscriber['active']}
                                             for subscriber in service_info['subscribers']]

        result_service['subsNum'] = str(len(service_info['subscribers'])) + '/' + str(service_info['subscribersNum'])
        result_service['startDatetime'] = str(service_info['startDatetime'])
        result_service['endDatetime'] = str(service_info['endDatetime'])
        result_service['active'] = 'Yes' if service_info['isRunning'] else 'No'
        is_owner = True if self.user.user == service_info['subscribers'][0]['userId'] else False
        result_service['isOwner'] = is_owner
        result_service['secretKey'] = service_info['secretKey'] if is_owner else ''
        result_service['permitRun'] = service_info['permitRun'] if is_owner else None
        result_service['isRunning'] = service_info['isRunning'] if is_owner else None

        response['message'] = 'success'
        response['content'] = result_service

        return response


class HTMHService(MongoDriver):
    def __init__(self):
        MongoDriver.__init__(self, db_name='Services')
        self.collection = self.db['Htmh']
        self.collection.create_index([('token', -1)])

    @property
    def pending_to_activate(self):
        query = {'isRunning': False, 'isUsable': True, 'permitRun': False}
        ready_to_activate = []
        for service in self.collection.find(query):
            now_time = datetime.datetime.now()
            active_subscribers = [subscriber for subscriber in service['subscribers'] if subscriber['active']]
            if len(active_subscribers) == service['subscribersNum'] and (
                    service['startDatetime'] <= now_time < service['endDatetime']):
                token = service['token']
                query = {'token': token}
                self.collection.update(
                    query,
                    {
                        '$set': {"permitRun": True}
                    }
                )
                ready_to_activate.append(service['token'])
        return ready_to_activate

    @property
    def expired(self):
        query = {'isUsable': True}
        expired = []
        for service in self.collection.find(query):
            if service['endDatetime'] <= datetime.datetime.now():
                token = service['token']
                query = {'token': token}
                self.collection.update(
                    query,
                    {
                        '$set': {"permitRun": False, 'isRunning': False, 'isUsable': False}
                    }
                )
                expired.append(token)
                for subscriber in service['subscribers']:
                    User(subscriber['userId']).actual_service = None

        return expired

    def activate_services(self, services: list):
        query = {'$or': [{'token': service_token} for service_token in services]}
        self.collection.update_many(
            query,
            {
                '$set': {"permitRun": True}
            }
        )

    def deactivate_services(self, services: list):
        query = {'$or': [{'token': service_token} for service_token in services]}
        self.collection.update_many(
            query,
            {
                '$set': {"permitRun": False, 'isRunning': False, 'isUsable': False}
            }
        )

    def set_running_service(self, token: ObjectId):
        query = {'token': token}
        self.collection.update(query, {'$set': {'isRunning': True}})

    def get_htmh_devices(self, token: ObjectId):
        query = {'token': token}
        subscribers = self.collection.find_one(query)['subscribers']
        devices = [subscriber['equipment'] for subscriber in subscribers]
        return devices


if __name__ == '__main__':
    user = User(user_id='00212345678')
    print(user.actual_service)
