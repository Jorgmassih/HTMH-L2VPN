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


class Config(MongoDriver):
    def __init__(self, db_name: str, doc: str):
        super().__init__(db_name)
        self.collection = self.db['Config']
        self.data_key = 'data'
        self.doc = doc

    def __getattr__(self, attr):
        coll = self.collection.find_one({'type': self.doc})
        data = coll[self.data_key]
        if attr in data:
            return data[attr]
        else:
            raise Exception('Invalid key')


if __name__ == '__main__':
    mongo = Config('NetworkStatus', 'connection')
    print(mongo.url)
