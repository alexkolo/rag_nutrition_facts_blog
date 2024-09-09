"""
Start app: `streamlit run dashboard/app.py --server.port 8080`
View in browser: `http://localhost:8080`
"""

import json
import os
from datetime import datetime

import pandas as pd
import pymongo
import streamlit as st
import tomli
from pymongo.collection import Collection

# Secrets
# -----------------------------
DEPLOYED: bool = st.secrets.get("deployed", False)

# Parameters
# -----------------------------
RAG_CONFIG_TOML: str = "rag_config.toml"


# Database Connection Functions
# -----------------------------


def get_mongodb_config(deployed: bool = False) -> dict[str, str]:
    key: str = "mongodb"

    # run as streamlit app
    if deployed:
        return st.secrets[key]

    # load local config file
    with open(RAG_CONFIG_TOML, mode="rb") as toml_file:
        config = tomli.load(toml_file)

    # running in a docker container
    if os.getenv("RUNNING_IN_DOCKER") is not None:
        return config[key]["docker"]

    # running locally
    return config[key]["local"]


# Setup MongoDB connection
# -----------------------------
mongodb_config: dict[str, str] = get_mongodb_config(DEPLOYED)
client = pymongo.MongoClient(mongodb_config["uri"])
db = client[mongodb_config["db_name"]]
collection: Collection = db[mongodb_config["coll_name"]]

# Database Query Helper Function
# -----------------------------


# Helper function to query data from MongoDB
def fetch_data_from_mongo(query: list[dict]) -> list[dict]:
    return list(collection.aggregate(query))


# Load query template from file
def load_query_template(filepath: str) -> list[dict]:
    with open(filepath, encoding="utf-8") as file:
        return json.load(file)


# Function to replace placeholders in the query with actual datetime values
def replace_time_in_query(query: list[dict], start_time: datetime, end_time: datetime) -> list[dict]:
    # Traverse the query structure and replace the placeholders with actual datetime objects
    for stage in query:
        if "$match" in stage.keys() and "convertedTimestamp" in stage["$match"].keys():
            stage["$match"]["convertedTimestamp"]["$gte"] = start_time
            stage["$match"]["convertedTimestamp"]["$lte"] = end_time
    return query


def get_values_from_query(query_template_path: str, start_time: datetime, end_time: datetime) -> list[dict]:
    query_template = load_query_template(query_template_path)
    panel_query: list[dict] = replace_time_in_query(query_template, start_time, end_time)
    return fetch_data_from_mongo(panel_query)


# Page starts here
# ==========================
page_title = 'Data Usage of "Nutrition Insights with Dr. Greger\'s Digital Twin 🥦" App'
st.set_page_config(page_title=page_title)

# Header
# -------------------------
st.title("Dashboard")
st.header(page_title)
st.write("Link to app: https://dr-greger-blog-bot.streamlit.app")

# Sidebar: Date Filter
# -------------------------
# Time range selection (mimicking Grafana's $__timeFrom and $__timeTo)
with st.sidebar:
    st.write("Date Filter:")
    day_offset: int = st.number_input("Last days", value=7, min_value=1)
    start_date = st.date_input("Start date", value=pd.to_datetime("now") - pd.DateOffset(day_offset))
    end_date = st.date_input("End date", value=pd.to_datetime("now"))

# Convert selected dates to datetime objects with time at the start and end of the day
start_time = datetime.combine(start_date, datetime.min.time())
end_time = datetime.combine(end_date, datetime.max.time())
date_filter: dict[str, datetime] = {"start_time": start_time, "end_time": end_time}

no_data_msg = f"No data available for the selected time range. {date_filter['start_time']} - {date_filter['end_time']}"

# Numbers Panel
# --------------------------
st.divider()
st.header("Numbers")
col_1, col_2 = st.columns(2, vertical_alignment="center")

if os.getenv("RUNNING_IN_DOCKER") is not None:
    query_root = "./"
else:
    query_root = "./dashboard/"

with col_1, st.container(border=True):
    st.subheader("# Users")
    panel_values: list[dict] = get_values_from_query(f"{query_root}query_n_user.json", **date_filter)
    value: int = panel_values[0]["totalEntries"] if panel_values else 0
    st.metric("Total Users", value, label_visibility="collapsed")

with col_2, st.container(border=True):
    st.subheader("Avg. User Rating")
    st.write("(0 = bad, 4 = very good)")
    panel_values: list[dict] = get_values_from_query(f"{query_root}query_avg_user_rating.json", **date_filter)
    avg_rating: float = panel_values[0]["averageScore"] if panel_values else 0
    st.metric("Avg. User Rating", round(avg_rating, 1), label_visibility="collapsed")

# Times Series Charts
# --------------------------
st.divider()
st.header("Times Series")


def create_ts_chart(query_template_path: str, y_key: str, y_label: str | None = None):
    panel_values: list[dict] = get_values_from_query(f"{query_root}{query_template_path}.json", **date_filter)
    time_series = pd.DataFrame(panel_values)
    if not time_series.empty:
        time_series["time"] = pd.to_datetime(time_series["_id"].apply(lambda x: x["time"]))
        time_series.set_index("time", inplace=True)
        st.line_chart(time_series[y_key], x_label="time", y_label=y_label)
    else:
        st.write(no_data_msg)


# Panel: Time Series of User Ratings
with st.container(border=True):
    st.subheader("User Ratings")
    st.write("(0 = bad, 4 = very good)")
    create_ts_chart("query_ts_user_rating", y_key="averageRating", y_label="user rating")

# Panel: Number of User Questions
with st.container(border=True):
    st.subheader("Number of User Questions")
    create_ts_chart("query_ts_n_quest", y_key="totalQuestions", y_label="# user questions")

# Panel: Average Characters of User Questions
with st.container(border=True):
    st.subheader("Avg. Characters per User Questions")
    create_ts_chart("query_ts_char_per_quest", y_key="avgQuestionLength", y_label="avg. char. per question")

# Panel: Average Number of Characters in Assistant's Answer
with st.container(border=True):
    st.subheader("Avg. Characters per Assistant's Answer")
    create_ts_chart("query_ts_chat_per_answer", y_key="avgAnswerLength", y_label="avg. char. per answer")
