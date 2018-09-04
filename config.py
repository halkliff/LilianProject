# Configurations file, which will be used as placeholder to all useful info
from bson.objectid import ObjectId
import Data
staff_db = Data.Database(Data.users_db.members)
ch_list = Data.Database(Data.channels_db.channels).search({})

DEV = False
BOT_SUDO = [] # Replace with all the admins user_id
if DEV:
    BOT_TOKEN = 'DEV_BOT_TOKEN'
else:
    BOT_TOKEN = 'PROD_BOT_TOKEN'


PHOTOS_CHANNEL = '' #Channel for the media tests
HALKSNET_CHANNEL = ''#Channel for the exclusive use of your network
PUB_CHANNEL = ''#DEPRECATED: publisher channel


FILES_MAIN = ObjectId('') # Create a document on the files collection and replace its ID here
ANALYTICS_MAIN = ObjectId('') #Create a document on the analytics collection and replace it's ID here


STAFF = [i['user_id'] for i in staff_db.search({})]

CHANNELS = []
