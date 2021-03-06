from pymongo import MongoClient
from bson.objectid import ObjectId
from random_object_id import generate
import datetime

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
        mongo_uri = "mongodb+srv://jorgmassih:Jamv1420290@htmh-db.ll4nf.gcp.mongodb.net/{}?retryWrites=true&w=majority".format(self.db_name)
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

    def _get_host_id(self, host: dict):
        if not host.get('deviceId'):
            host = self.convert_host_format(host)

        mac = host['mac']
        device_id = str(host['deviceId'])[8:]
        return '{}-{}'.format(mac, device_id)

    @hosts.setter
    def hosts(self, hosts: list):
        collection = self.db['AnatomyHosts']
        collection.delete_many({})
        for i in range(len(hosts)):
            if not hosts[i].get('deviceId'):
                hosts[i] = self.convert_host_format(host=hosts[i])

        collection.insert_many(hosts)

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

    def insert_host(self, host: dict):
        pass

    def insert_link(self, link: dict):
        collection = self.db['AnatomyLinks']
        link_id = '{}-{}-{}-{}'.format(link['src']['device'], link['src']['port'],
                                       link['dst']['device'], link['dst']['port'])
        link['_id'] = link_id
        collection.insert_one(link)

    def compare_host(self, hosts_to_compare: list):
        pass

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


class UserNetworkAnatomy(MongoDriver):
    def __init__(self, user_id: str):
        MongoDriver.__init__(self, db_name='NetworkStatus')
        self.device_id = User(user_id=user_id).equipment_id

    def get_devices_list(self):
        collection = self.db['AnatomyHosts']
        query = {'deviceId': self.device_id}
        hosts = []
        keys_to_filter = ['mac', 'ip', 'virtualIp', 'friendlyName', ]
        for host in collection.find(query):
            filtered = dict((k, host[k]) for k in keys_to_filter if k in host)
            hosts.append(filtered)

        return hosts

    def change_friendly_name(self, mac: str, new_friendly_name: str):
        collection = self.db['AnatomyHosts']
        query = {'mac': mac, 'deviceId': self.device_id}
        update = collection.find_one_and_update(filter=query, update={'$set': {'friendlyName': new_friendly_name}},
                                                upsert=False, return_document=True)

        return True if update else False


class User(MongoDriver):
    def __init__(self, user_id: str):
        MongoDriver.__init__(self, db_name='UserInfo')
        self.collection = self.db['User']
        self.user = ObjectId('0'*13 + user_id)

    @property
    def user_str(self):
        user = str(self.user)[-11:]
        return user

    def is_logged(self):
        print(self.user)
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
        actual_service = self.collection.find_one(filter=query)['actualService']

        return actual_service

    @actual_service.setter
    def actual_service(self, service_token):
        self.collection.update_one({'documentId': self.user}, {'$set': {'actualService': service_token}})

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
        self.user_id = User.user_str
        MongoDriver.__init__(self, db_name='Services')

    @property
    def user_col(self):
        self.db_name = 'UserInfo'
        return self.db['User']

    @property
    def serv_col(self):
        self.db_name = 'Services'
        return self.db['Htmh']

    @property
    def service_token(self):
        user_col = self.user_col
        # serv_col = self.serv_col
        user = user_col.find_one({'documentId': self.user.user})
        token = user['actualService']
        return token

    @property
    def htmh_subscribers(self):
        service = self.serv_col.find_one({'token': self.user.actual_service})
        response = None
        subscribers_list = []

        if not service:
            response = 'This user is not subscribed to any service'
            return {'response': response, 'subs_list': subscribers_list}

        subscribers_list = [{'userId': str(subscriber['userId'])[-11:],
                             'name': subscriber['name'],
                             'equipment': str(subscriber['equipment'])[-16:]}
                            for subscriber in service['subscribers'] if subscriber['userId'] != self.user.user]

        return {'response': response, 'subs_list': subscribers_list}

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

        if (content['endDatetime'] - content['startDatetime']).total_seconds()/60 < 30:
            response['message'] = 'Service minimum time is 30 minutes'
            return response

        service_token = ObjectId(generate())
        content['token'] = service_token

        if not self.user.actual_service:
            self.user.actual_service = service_token
            content['subscribers'].append({'name': self.user.fullname,
                                           'equipment': self.user.equipment_id,
                                           'userId': self.user.user})
        else:
            response['message'] = 'The User is already on another service'
            return response

        collec = self.serv_col
        inserting = collec.insert_one(content).inserted_id
        response['message'] = 'success'
        response['serviceToken'] = str(content['token'])
        return response

    def add_user_to(self, content):
        response = None

        collec = self.serv_col
        token = ObjectId(content['serviceToken'])
        secret_key = content['secretKey']
        service = collec.find_one({'token': token})

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
                                       'userId': self.user.user})

        new_values = {"$set": service}

        self.user.actual_service = token

        collec.update_one({'token': token}, new_values)

        return response

    def kill_one(self):
        # user_db = Mongo.UserInfo
        user_col = self.user_col
        serv_col = self.serv_col
        response = {'message': None}
        # token = request.args.get('token')
        if self.service_token is None:
            response['message'] = 'Service not found'
            return response
        service = serv_col.find_one({'token': ObjectId(self.service_token)})

        if service is None or not service['isUsable']:
            response['message'] = 'Service not existing'
            return response
        # print(service['usersId'])

        if service['usersId'].index(ObjectId(self.user_id)) != 0:
            service['usersId'].remove(ObjectId(self.user_id))
            user_col.update_one({'documentId': ObjectId(self.user_id)}, {'$set': {'actualService': None}})
            serv_col.update_one({'token': ObjectId(self.service_token)}, {'$set': {'usersId': service['usersId']}})
            response['message'] = 'success'
            return response

        for userId in service['usersId']:
            # print(user_col.find_one({'documentId': userId}))
            user_col.update_one({'documentId': userId}, {'$set': {'actualService': None}})
        serv_col.update_one({'token': ObjectId(self.service_token)}, {'$set': {'isUsable': False}})
        response['message'] = 'success'
        return response

    def show_one(self):
        response = {'message': None, 'content': None}

        serv_col = self.serv_col
        if self.user.actual_service is None:
            response['message'] = 'Service not found'
            return response

        service_info = serv_col.find_one({'token': self.user.actual_service})

        if service_info is None or not service_info['isUsable']:
            response['message'] = 'Service not existing'
            return response

        result_service = dict()

        result_service['serviceToken'] = str(service_info['token'])

        result_service['subscribersList'] = [{'name': subscriber['name'],
                                              'equipment': str(subscriber['equipment'])[-16:]}
                                             for subscriber in service_info['subscribers']]

        result_service['subsNum'] = str(len(service_info['subscribers'])) + '/' + str(service_info['subscribersNum'])
        result_service['startDatetime'] = str(service_info['startDatetime'])
        result_service['endDatetime'] = str(service_info['endDatetime'])
        result_service['active'] = 'Yes' if service_info['isRunning'] else 'No'
        is_owner = True if self.user.user == service_info['subscribers'][0]['userId'] else False
        result_service['isOwner'] = is_owner
        result_service['secretKey'] = service_info['secretKey'] if is_owner else ''
        result_service['permitRun'] = service_info['permitRun'] if is_owner else None

        response['message'] = 'success'
        response['content'] = result_service

        return response
