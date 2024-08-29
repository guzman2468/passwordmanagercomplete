from pymongo import MongoClient
import config

class Database:
    def __init__(self, db_name='password_manager'):
        self.client = MongoClient(config.uri)
        self.db = self.client[db_name]

    def get_collection(self, collection_name='passwords'):
        return self.db[collection_name]

if __name__ == "__main__":
    db = Database()
    collection = db.get_collection()
    print(f"Connected to collection: {collection.name}")