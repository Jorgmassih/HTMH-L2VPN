from pymongo import MongoClient
from bson.objectid import ObjectId


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
    def __init__(self, db_name: str):
        super().__init__(db_name)

    @property
    def hosts(self):
        return {}

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

    def compare_links(self, links_to_compare: list):
        ids_to_compare = set()
        for link in links_to_compare:
            link_id = '{}-{}-{}-{}'.format(link['src']['device'], link['src']['port'],
                                           link['dst']['device'], link['dst']['port'])
            ids_to_compare.add(link_id)

        return self.links_ids - ids_to_compare, ids_to_compare - self.links_ids


class User(MongoDriver):
    def __init__(self, user_id: str):
        MongoDriver.__init__(self, db_name='UserInfo')
        self.collection = self.db['User']
        self._user = ObjectId('0'*13 + user_id)

    def is_logged(self):
        print(self._user)
        query = {"documentId": self._user, "webApp.logged": True}

        return True if self.collection.find_one(query) else False

    def login(self, password):
        query = {"documentId": self._user, "webApp.logged": False, "webApp.password": password}
        update = self.collection.find_one_and_update(filter=query, update={'$set': {'webApp.logged': True}},
                                                     upsert=False, return_document=True)
        if not update:
            print('Entry not found at login')
            return False

        return True

    def logout(self):
        query = {"documentId": self._user, "webApp.logged": True}
        update = self.collection.find_one_and_update(filter=query, update={'$set': {'webApp.logged': False}},
                                                     upsert=False, return_document=True)
        if not update:
            print('Entry not found at login')
            return False

        return True


if __name__ == '__main__':
    user = User('00512345678')

    print(user.logout())
