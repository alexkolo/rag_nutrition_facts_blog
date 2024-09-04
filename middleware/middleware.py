import os
from datetime import datetime, timezone
from typing import Any

from flask import Flask, jsonify, request
from pymongo import MongoClient

app = Flask(__name__)

# Environment variables
uri = os.getenv("MONGODB_URI_DOCKER")
db_name = os.getenv("MONGODB_DB_NAME")
coll_name = os.getenv("MONGODB_COLL_NAME")

# MongoDB connection
client = MongoClient(uri)
db = client[db_name]
collection = db[coll_name]


def replace_time_placeholders(pipeline: list[dict[str, Any]], time_from: datetime, time_to: datetime) -> None:
    """
    Recursively replaces Grafana time range placeholders ($__timeFrom, $__timeTo) in a MongoDB
    aggregation pipeline with actual datetime values.

    Parameters
    ----------
    pipeline : List[Dict[str, Any]]
        The MongoDB aggregation pipeline where placeholders need to be replaced.
    time_from : datetime
        The start time for the time range, replacing the $__timeFrom placeholder.
    time_to : datetime
        The end time for the time range, replacing the $__timeTo placeholder.

    Returns
    -------
    None
        The function modifies the pipeline in place and does not return any value.
    """
    # Iterate over each stage in the aggregation pipeline
    for stage in pipeline:
        # Iterate over each key-value pair in the stage
        for key, value in stage.items():
            if isinstance(value, dict):
                # Recursively call the function if the value is a dictionary
                replace_time_placeholders(value, time_from, time_to)
            elif isinstance(value, list):
                # Recursively call the function for each item if the value is a list
                for item in value:
                    if isinstance(item, dict):
                        replace_time_placeholders(item, time_from, time_to)
            elif isinstance(value, str):
                # Replace placeholders with actual datetime values
                if value == "$__timeFrom":
                    stage[key] = time_from
                elif value == "$__timeTo":
                    stage[key] = time_to


@app.route("/search", methods=["POST"])
def search():
    return jsonify(["custom_metric"])


@app.route("/test", methods=["GET"])
def test():
    return jsonify({"status": "ok"})


@app.route("/query", methods=["POST"])
def query():
    req = request.get_json()
    target_metric = req["targets"][0]["target"]

    if target_metric == "custom_metric":
        # Extract the aggregation pipeline from the request
        pipeline = req.get("pipeline", [])

        if "range" in req:
            # Extract time range from the request (adjust format as needed)
            time_from = datetime.fromtimestamp(req["range"]["from"] / 1000, timezone.utc)
            time_to = datetime.fromtimestamp(req["range"]["to"] / 1000, timezone.utc)

            # Replace Grafana placeholders with actual time values
            replace_time_placeholders(pipeline, time_from, time_to)

        # Execute the aggregation pipeline on MongoDB
        cursor = collection.aggregate(pipeline)

        # Format the results to match Grafana's expected format
        datapoints = [[doc.get("value"), doc.get("time")] for doc in cursor]

        return jsonify([{"target": target_metric, "datapoints": datapoints}])

    return jsonify([])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
