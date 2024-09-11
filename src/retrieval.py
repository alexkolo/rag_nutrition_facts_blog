import lancedb
import pandas as pd
from lancedb.db import DBConnection
from lancedb.rerankers import CrossEncoderReranker
from lancedb.table import Table

from src.constants import LANCEDB_URI, get_rag_config


def connect_to_lancedb_table(uri: str, table_name: str) -> Table:
    db: DBConnection = lancedb.connect(uri=uri)
    return db.open_table(table_name)


def get_knowledge_base(table_name: str | None = None) -> Table:
    db: DBConnection = lancedb.connect(uri=LANCEDB_URI)
    _table_name: str = table_name or get_rag_config()["knowledge_base"]["table_name"]
    return db.open_table(_table_name)


def retrieve_context(
    k_base: Table, query_text: StopIteration, n_retrieve: int = 10, rr_model_name: str = "", device: str | None = None
) -> list[dict]:
    # Use `weight` as the weight for vector search (instead of 0.7)
    # reranker_lc = LinearCombinationReranker(weight=weight)
    # reranker_rrf = RRFReranker()
    # https://lancedb.github.io/lancedb/reranking/cross_encoder/
    _device = device or get_rag_config()["reranker"]["device"]
    _rr_model_name = get_rag_config()["reranker"]["model_name"] if rr_model_name == "" else rr_model_name
    rr_cross_encoder = CrossEncoderReranker(model_name=_rr_model_name, device=_device)

    return (
        k_base.search(query=query_text, query_type="hybrid")
        .rerank(reranker=rr_cross_encoder)
        .limit(n_retrieve)
        .to_list()
    )


def reorder_context(resp: list[dict], n_use: int = 5) -> list[dict]:
    # Pandas Pipeline
    return (
        # Create a DataFrame
        pd.DataFrame(resp)
        # Remove 'vector' column
        .drop(columns=["vector"])
        # remove duplicates based on 'hash_doc'
        .drop_duplicates(subset="hash_doc")
        # Group paragraphs by 'title'
        .groupby("title")
        .agg(
            para=("text", list),  # collect all 'text' into a list per title
            score_sum=("_relevance_score", "sum"),  # sum 'score' for each title
            para_count=("text", "count"),  # count 'text' for each title
            url=("url", "first"),  # take the 1st URL since it's the same for an entire group
        )
        .reset_index()  # moves "title" from index to column
        .sort_values(by="score_sum", ascending=False)  # sort by 'score_sum'
        # .reset_index(drop=True)  # renew index
        # Add a cumulative count column based on 'text_count'
        .assign(cum_count=lambda x: x["para_count"].cumsum())
        .iloc[:n_use]  # get the first `n_use` titles
        .to_dict("records")  # convert to `list[dict]`
    )


def format_context(resp: list[dict]) -> str:
    # Initialize an empty list to store the formatted strings
    output_lines = []

    # Iterate through each row in the grouped_df
    for i, row in enumerate(resp):
        # Add the title line
        output_lines.append(f"{i + 1}. Title '{row['title']}' (URL: {row['url']}):")

        # Add each text (para) under the title
        for para in row["para"]:
            output_lines.append(f"\t- {para}")

    # Join all lines into a single string with newline characters
    return "\n".join(output_lines)


def get_context(k_base: Table, query_text: str, n_use: int = 5, **kwargs) -> str:
    cxt_raw: list[dict] = retrieve_context(k_base=k_base, query_text=query_text, **kwargs)
    cxt_reordered: list[dict] = reorder_context(cxt_raw, n_use=n_use)
    cxt_string: str = format_context(cxt_reordered)

    return cxt_string
