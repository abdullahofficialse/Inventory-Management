from pymongo import MongoClient, collection,database
import os 
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("project1ab"))
db = client["project1"]
collection = db["customers"]
collection2 = db["transactions"]
collection3 = db["products"]
collection4 = db["categories"]
collection5=db["authentication"]
