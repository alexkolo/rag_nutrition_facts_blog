"""
Start app: `streamlit run dashboard/app.py --server.port 8080`
View in browser: `http://localhost:8080`
"""

import json
import os
from datetime import datetime
from pathlib import Path

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


def load_and_replace_value_key(filepath: str | Path, value_key: str = "") -> list[dict]:
    # Load the JSON query from the file
    with open(filepath, encoding="utf-8") as file:
        query = json.load(file)

    if value_key:
        # Convert the query to a string for replacement
        query_str = json.dumps(query)

        # Replace all instances of {{value_key}} with the input value_key
        query_str = query_str.replace("{{value_key}}", value_key)

        # Convert the string back to JSON format
        return json.loads(query_str)

    return query


# Function to replace placeholders in the query with actual datetime values
def replace_time_in_query(query: list[dict], start_time: datetime, end_time: datetime) -> list[dict]:
    # Traverse the query structure and replace the placeholders with actual datetime objects
    for stage in query:
        if "$match" in stage.keys() and "convertedTimestamp" in stage["$match"].keys():
            stage["$match"]["convertedTimestamp"]["$gte"] = start_time
            stage["$match"]["convertedTimestamp"]["$lte"] = end_time
    return query


def get_values_from_query_file(
    query_file: str | Path,
    start_time: datetime,
    end_time: datetime,
    value_key: str = "",
) -> list[dict]:
    query_dict: list[dict] = load_and_replace_value_key(filepath=query_file, value_key=value_key)
    panel_query: list[dict] = replace_time_in_query(query_dict, start_time, end_time)
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
    end_date_default = pd.to_datetime("now")
    days_between: int = (end_date_default - pd.to_datetime("2024-09-02")).days

    day_offset: int = st.number_input("Last days", value=days_between, min_value=1)
    start_date = st.date_input("Start date", value=end_date_default - pd.DateOffset(day_offset))
    end_date = st.date_input("End date", value=end_date_default)

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
    panel_values: list[dict] = get_values_from_query_file(f"{query_root}query_n_user.json", **date_filter)
    value: int = panel_values[0]["totalEntries"] if panel_values else 0
    st.metric("Total Users", value, label_visibility="collapsed")

with col_2, st.container(border=True):
    st.subheader("Avg. User Rating")
    st.write("_(0 = the worst, 4 = the best)_")
    panel_values: list[dict] = get_values_from_query_file(f"{query_root}query_avg_user_rating.json", **date_filter)
    avg_rating: float = panel_values[0]["averageScore"] if panel_values else 0
    st.metric("Avg. User Rating", round(avg_rating, 1), label_visibility="collapsed")

# Charts
# --------------------------
st.divider()
st.header("Charts")


def create_ts_chart(
    query_template: str,
    y_key: str,
    value_key: str = "",
    y_label: str | None = None,
    fillna: bool = False,
):
    panel_values: list[dict] = get_values_from_query_file(
        query_file=f"{query_root}{query_template}.json", value_key=value_key, **date_filter
    )
    table = pd.DataFrame(panel_values)
    if not table.empty:
        # extract date information
        table["time"] = pd.to_datetime(table["_id"].apply(lambda x: x["time"]))
        # extract time series
        time_series: pd.Series = table.set_index("time")[y_key]
        if fillna:
            time_series = time_series.fillna(0)
        else:
            time_series = time_series.dropna()
        # plot time series
        st.line_chart(data=time_series, x_label="time", y_label=y_label)
        # show data points
        with st.expander(f"`{time_series.shape[0]} data points used`"):
            st.write(time_series)
    else:
        st.write(no_data_msg)


# Panel: Time Series of User Ratings
st.subheader("User Ratings")
with st.container(border=True):
    st.write("_(0 = the worst, 4 = the best)_")
    create_ts_chart("query_ts_user_rating", y_key="averageRating", y_label="user rating")

# Panel: Number of User Questions
st.subheader("Number of Questions per User")
with st.container(border=True):
    create_ts_chart("query_ts_n_quest", y_key="totalQuestions", y_label="# user questions")


# LLM Usage
# ----------------
# st.divider()
st.subheader("Avg. LLM usage per Q&A")
st.write("_Only tracked since 09/09/2024._")
for value_keys, label in [
    (["prompt_tokens", "completion_tokens", "total_tokens"], "token"),
    (["prompt_time", "completion_time", "total_time"], "time (s)"),
]:
    values_dict = {}
    for value_key in value_keys:
        panel_values: list[dict] = get_values_from_query_file(
            query_file=f"{query_root}query_ts_llm_usage.json", value_key=value_key, **date_filter
        )
        table = pd.DataFrame(panel_values)
        # extract date information
        table["time"] = pd.to_datetime(table["_id"].apply(lambda x: x["time"]))
        # extract time series
        values_dict[value_key] = table.set_index("time")["avgValue"]

    # table = pd.DataFrame(values_dict).dropna(how="all", axis=0).loc[lambda x: (x != 0).any(axis=1)]
    table = pd.DataFrame(values_dict).fillna(0)  # .loc[lambda x: (x != 0).any(axis=1)]
    with st.container(border=True):
        st.write(f"**Average {label.capitalize()} Usage per Q&A**")
        # plot time series
        st.line_chart(data=table, x_label="time", y_label=f"avg. {label} usage per Q&A")
        # show data points
        with st.expander(f"`{table.shape[0]} data points`"):
            st.write(table)

# Panel: Assistant response time (s) per user question
with st.container(border=True):
    st.write("**Assistant response time (s) per user question**")
    create_ts_chart("query_ts_rsp_time", y_key="avgResponseTime", y_label="response time (s)", fillna=True)


# Various Panels
# ----------------
st.divider()
st.header("Various Stats")

# Panel: Average Characters of User Questions
with st.container(border=True):
    st.write("**Avg. Characters per User Questions**")
    create_ts_chart("query_ts_char_per_quest", y_key="avgQuestionLength", y_label="avg. char. per question")

# Panel: Average Number of Characters in Assistant's Answer
with st.container(border=True):
    st.write("**Avg. Characters per Assistant's Answer**")
    create_ts_chart("query_ts_chat_per_answer", y_key="avgAnswerLength", y_label="avg. char. per answer")
