from pymongo import MongoClient


class MongoDriver():
    def __init__(self, db_name):
        self.db_name = db_name
        self.client = MongoClient(self.mongo_uri)

    @property
    def mongo_uri(self):
        mongo_uri = "mongodb+srv://jorgmassih:Jamv1420290@htmh-db.ll4nf.gcp.mongodb.net/{}?retryWrites=true&w=majority".format(self.db_name)
        return mongo_uri


if __name__ == '__main__':
    mongo = MongoDriver('NetworkStatus')
