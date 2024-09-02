from typing import Any

import streamlit as st
from pymongo.collection import Collection
from pymongo.mongo_client import MongoClient


# Uses st.cache_resource to only connect once per day
@st.cache_resource(ttl="1 day", show_spinner=True)
def init_mongodb_connection(uri: str) -> MongoClient:
    # Initialize connection.
    return MongoClient(uri)


class MongodbClient:
    def __init__(self, uri: str, db_name: str, coll_name: str):
        self.mongodb_client: MongoClient = init_mongodb_connection(uri)
        self.db_name: str = db_name
        self.coll_name: str = coll_name

    def ping(self):
        # test connection
        self.mongodb_client.admin.command("ping")

    def connection_test(self):
        try:
            self.ping()
            return True
        except Exception:
            return False

    def get_database(self):
        return self.mongodb_client[self.db_name]

    def get_collection(self) -> Collection:
        database = self.get_database()
        return database[self.coll_name]

    def find(self, filter: dict | None = None, limit=0) -> list[dict[str, Any]]:
        collection = self.get_collection()
        items = list(collection.find(filter=filter if filter else {}, limit=limit))
        return items

    def find_one(self, filter: dict | None = None):
        collection = self.get_collection()
        return collection.find_one(filter=filter if filter else {})

    def find_many(self, filter: dict | None = None, limit: int | None = None):
        collection = self.get_collection()
        if limit is None or limit < 1:
            return collection.find(filter if filter else {})
        return collection.find(filter if filter else {}).limit(limit)

    def insert_one(self, new_entry: dict[str, Any]):
        collection = self.get_collection()
        collection.insert_one(new_entry.copy())

    def upsert_one(self, filter: dict, new_entry: dict[str, Any]):
        collection = self.get_collection()
        collection.update_one(filter, {"$set": new_entry})

    def update_single_field(self, filter: dict, field: str, value: Any):
        new_entry: dict[str, Any] = {field: value}
        self.upsert_one(filter, new_entry)

    def delete_one(self, filter: dict):
        collection = self.get_collection()
        collection.delete_one(filter)


def save_chat_history(
    mongodb_client: MongodbClient,
    user_id: str,
    n_sessions: int,
    chat_history: list[dict[str, str]],
    retrieval: list[str] | None = None,
):
    filter: dict[str, str] = {"user_id": user_id}
    if n_sessions == 1:
        # need to create the nested field first
        mongodb_client.upsert_one(filter, {"chat_history": {"1": chat_history}})
        if retrieval is not None:
            mongodb_client.upsert_one(filter, {"retrieval": {"1": retrieval}})
    else:
        # this will add a new nested field
        mongodb_client.upsert_one(filter, {f"chat_history.{n_sessions}": chat_history})
        if retrieval is not None:
            mongodb_client.upsert_one(filter, {f"retrieval.{n_sessions}": retrieval})

    mongodb_client.upsert_one(filter, {"n_sessions": n_sessions})
