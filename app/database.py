import os
import certifi
from pymongo import MongoClient
from dotenv import load_dotenv

# 載入 .env 環境變數
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "keelung_db")

# 初始化 MongoClient，加入 certifi CA 憑證檔解決 macOS SSL CERTIFICATE_VERIFY_FAILED 錯誤
try:
    client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where())
except Exception:
    client = MongoClient(MONGODB_URI)

db = client[DB_NAME]


def get_database():
    """取得 MongoDB 資料庫物件"""
    return db
