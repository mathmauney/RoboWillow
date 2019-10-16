import pymongo
from trade_functions import *

my_client = pymongo.MongoClient("mongodb://mathmauney.no-ip.org:27017/")
trade_db = my_client['trade_test']
users = trade_db['users']
offers = trade_db['offers']
