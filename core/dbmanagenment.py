import json
import os
from core.constants import getlog, DBPATH

class DbClient(object):
    def __init__(self, database=None, collection=None):
        self.log = getlog()
        self.database = database
        self.collection = collection
        self.users_file = DBPATH
        self.users = self._load_users()

    def _load_users(self):
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_users(self):
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f)

    def conectdb(self):
        return True  # No connection needed for file-based storage

    def check_field(self):
        if self.database is None or self.collection is None:
            self.log.error("Please choose database name or collection")
            return False
        return True

    def set_database(self, database):
        self.database = database

    def set_collection(self, collection):
        self.collection = collection

    def collections(self):
        if self.check_field() is False:
            return
        return [self.collection]  # Only one collection for file-based storage

    def databases(self):
        return [self.database]  # Only one database for file-based storage

    def check_being(self, filter):
        username = filter.get('_id')
        return 1 if username in self.users else 0

    def get_collection(self):
        return self.users

    def insert(self, item):
        try:
            username = item.get('_id')
            if username in self.users:
                self.log.error(f"User {username} already exists")
                return -1  # duplicate
            self.users[username] = item
            self._save_users()
            self.log.info(f"User Registered Successfully: {username}")
            return 0
        except Exception as exp:
            self.log.error(repr(exp))
            return -2

    def get_documents(self, filter):
        try:
            username = filter.get('_id')
            if username in self.users:
                return self.users[username]
            return -1
        except Exception as exp:
            return -1

"""
data=DbClient("P2PApp","authentication")



print(data.get_documents(filter={"_id": "fatih",}))
"""