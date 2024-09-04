import os

from flask import Flask, jsonify, request
from pymongo import MongoClient

app = Flask(__name__)

uri: str = os.getenv("MONGODB_URI_DOCKER")
db_name = os.getenv("MONGODB_DB_NAME")
coll_name = os.getenv("MONGODB_COLL_NAME")

# MongoDB connection
client = MongoClient(uri)  # Use 'mongodb' as the host to connect to the MongoDB service
db = client[db_name]
collection = db[coll_name]


@app.route("/search", methods=["POST"])
def search():
    return jsonify(["metric1"])


@app.route("/query", methods=["POST"])
def query():
    req = request.get_json()
    target_metric = req["targets"][0]["target"]  # Assuming a single target

    if target_metric == "metric1":
        cursor = collection.find({"field": "value"})
        datapoints = [[doc["metric_value"], doc["timestamp"]] for doc in cursor]

        return jsonify([{"target": target_metric, "datapoints": datapoints}])

    return jsonify([])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
