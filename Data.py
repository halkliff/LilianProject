import pymongo
client = pymongo.MongoClient('localhost', 27017)

analytics_db = client.analytics
channels_db = client.channels
files_db = client.files
users_db = client.users


class Database:

    def __init__(self, storage):
        self.storage = storage

    def write(self, data):
        if not isinstance(data, dict):
            raise AttributeError("Error in data: {}\n Data shall be a dict!".format(data))
        return self.storage.insert_one(data).inserted_id

    def write_many(self, data):
        if not isinstance(data, list):
            raise AttributeError("Data must be a list!")

        for i in data:
            if not isinstance(i, dict):
                raise AttributeError("Error in data: {}\n Data shall be a dict!".format(i))

        return self.storage.insert_many(data).inserted_ids

    def update(self, cond, data):
        if not isinstance(data, dict):
            raise AttributeError("Error in data: {}\n Data shall be a dict!".format(data))

        if not isinstance(cond, dict):
            raise AttributeError("Error in condition: {}\n Condition shall be a dict!".format(cond))
        return self.storage.update_one(cond, data)

    def update_many(self, cond, data):
        if not isinstance(data, dict):
            raise AttributeError("Error in data: {}\n Data shall be a dict!".format(data))

        if not isinstance(cond, dict):
            raise AttributeError("Error in condition: {}\n Condition shall be a dict!".format(cond))

        return self.storage.update_many(cond, data)

    def delete(self, cond):
        if not isinstance(cond, dict):
            raise AttributeError("Error in condition: {}\n Condition shall be a dict!".format(cond))
        return self.storage.delete_one(cond)

    def delete_many(self, cond):
        if not isinstance(cond, dict):
            raise AttributeError("Error in condition: {}\n Condition shall be a dict!".format(cond))
        return self.storage.delete_many(cond)

    def search(self, cond):
        if not isinstance(cond, dict):
            raise AttributeError("Error in condition: {}\n Condition shall be a dict!".format(cond))
        return [i for i in self.storage.find(cond)]

    def get(self, cond=None):
        if not isinstance(cond, dict):
            raise AttributeError("Error in condition: {}\n Condition shall be a dict!".format(cond))
        return self.storage.find_one(cond)

    def all(self):
        return [i for i in self.storage.find()]


"""anime = -1001037927699
ecchi = -1001042354945
loli = -1001093976878
yuri = -1001036374497
hentai = -1001005214861
yaoi = -1001038568800
cosplay = -1001049542939
erocosplay = -1001013533259
kemonomimi = -1001081106735
furry = -1001084579591
erotic = -1001092105000"""

# print(Database(channels_db.channels).search({'channel_id': -1001241675894}))
# Database(users_db.members).update_many({}, {'$pullAll': {'owned_channels': [-1001126225612]}})
# print(Database(users_db.members).get({'user_id': 191792795}))
# print(Database(users_db.members).get({'user_id': 123956344})['owned_channels'])
# print(Database(users_db.members).get({'authorized_channels': -1001132758250}))
# print(Database(channels_db.channels).search({'channel_id': -1001132758250}))
# print(Database(files_db.files).search({'channel': -1001132758250}))
# '4f17X0O4'  '4f1880vC'
