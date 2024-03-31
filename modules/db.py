from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

load_dotenv()

def initcon():
    uri = os.getenv("murl")
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client.get_database("dlu")
    return db
db = initcon()