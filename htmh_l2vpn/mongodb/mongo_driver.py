from pymongo import MongoClient


class MongoDriver():
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
        return []

    @property
    def core_devices(self):
        return []

    @property
    def links(self):
        return []

    @links.setter
    def links(self, new_links: dict):
        pass

    def insert_host(self, host: dict):
        pass

    def insert_link(self, link: dict):
        pass

    def compare_links(self, link: dict):
        pass


if __name__ == '__main__':
    mongo = GetConfig('NetworkStatus')
    mongo.collection = 'Endpoints'
    mongo.doc = 'hosts_info'
    print(mongo.get_hosts)
