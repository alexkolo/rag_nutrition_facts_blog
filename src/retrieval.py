from typing import Any

import lancedb
import numpy as np
import pandas as pd
from lancedb.db import DBConnection
from lancedb.rerankers import CrossEncoderReranker
from lancedb.rerankers.base import Reranker
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
    k_base: Table,
    query_text: str,
    reranker: dict,
    n_retrieve: int = 10,
) -> list[dict]:
    """
    Retrieve most relevant text chunks using a hybrid search and rerank results with a cross-encoder model.

    Parameters
    ----------
    k_base : Table
        The knowledge base (table) from which to retrieve documents or text.
    query_text : str
        The query string used to search the knowledge base.
    reranker: dict
        The configuration for the cross-encoder model to use for reranking.
    n_retrieve : int, optional
        The number of relevant documents or text chunks to retrieve. Default is 10.

    Returns
    -------
    list[dict]
        A list of dictionaries, each representing a retrieved document or text chunk,
        including metadata and relevance score.

    Notes
    -----
    This function performs hybrid search and reranks the results using a cross-encoder
    model specified in the RAG (retrieval-augmented generation) configuration. It fetches
    the top `n_retrieve` text chunks from the knowledge base after reranking.

    References
    ----------
    - https://lancedb.github.io/lancedb/reranking/cross_encoder/
    """

    # Configure reranker
    device: str = reranker["device"]
    rr_model_name: str = reranker["model_name"]
    rr_cross_encoder: Reranker = CrossEncoderReranker(model_name=rr_model_name, device=device)

    # Retrieve `n_retrieve` most relevant text chunks
    return (
        k_base.search(query=query_text, query_type="hybrid")
        .rerank(reranker=rr_cross_encoder)
        .limit(n_retrieve)
        .to_list()
    )


def group_chunks_by_title(resp: list[dict], n_titles: int = 5) -> list[dict]:
    """
    Group retrieved text chunks by title, aggregate information, and return the top titles based on relevance score.

    Parameters
    ----------
    resp : list[dict]
        A list of dictionaries, where each dictionary represents a retrieved text chunk and its metadata,
        including 'hash_doc', 'hash_title', 'url', 'text', 'rank_abs', 'rank_rel', and '_relevance_score'.
    n_titles : int, optional
        The number of top titles to return, sorted by their cumulative relevance score. Default is 5.

    Returns
    -------
    list[dict]
        A list of dictionaries, where each dictionary represents a blog post or document, including
        aggregated information such as the list of text chunks, their ranks, relevance score, and the URL.

    Notes
    -----
    This function:
    1. Removes duplicate entries based on 'hash_doc'.
    2. Groups the text chunks by 'title'.
    3. Aggregates information such as 'hash_title', 'url', text chunk lists, and relevance scores.
    4. Sorts the results based on the sum of relevance scores ('score_sum').
    5. Returns the top `n_titles` titles, based on their relevance score.
    6. Adds a cumulative count of retrieved chunks ('cum_count'), although this field is not used directly.

    The resulting list contains one dictionary per title, where each dictionary includes:
    - 'hash_title': Unique identifier for the blog post.
    - 'url': URL of the blog post.
    - 'n_docs': Number of text chunks in the blog post.
    - 'chunks': List of text chunks for the blog post.
    - 'rank_abs': List of absolute ranks of the text chunks.
    - 'rank_rel': List of relative ranks of the text chunks.
    - 'score_sum': Total relevance score for the blog post.
    - 'n_chunks': Number of retrieved text chunks for the blog post.
    - 'cum_count': Cumulative count of the retrieved text chunks.
    """

    # Pandas Chain
    return (
        # Create a DataFrame
        pd.DataFrame(resp)
        # remove duplicates based on 'hash_doc'
        .drop_duplicates(subset="hash_doc")
        # Group paragraphs by 'title'
        .groupby("title")
        .agg(
            # First entry aggregation for unique fields
            hash_title=("hash_title", "first"),  # Unique ID of blog post (as a hash of the url + title)
            url=("url", "first"),  # URL of blog post
            n_docs=("n_docs", "first"),  # Number of total text chunks in the blog post
            # Collect lists of text and ranks
            chunks=("text", list),  # collect all text chunks of a blog post into a list
            rank_abs=("rank_abs", list),  # collect absolute ranks of the text chunks in the blog post
            rank_rel=("rank_rel", list),  # collect Relative ranks of the text chunks in the blog post
            # Compute
            score_sum=("_relevance_score", "sum"),  # sum relevance score of all text chunks of a blog post
            n_chunks=("text", "count"),  # Count Retrieved text chunks per blog post
        )
        # convert "title" from index to column
        .reset_index()
        # sort titles by 'score_sum' (the cumulative relevance score)
        .sort_values(by="score_sum", ascending=False)
        # Add a cumulative count of the 'n_chunks' column (not used at the moment)
        .assign(cum_count=lambda x: x["n_chunks"].cumsum())
        # return only the first `n_use` titles
        .iloc[:n_titles]
        # convert to `list[dict]`
        .to_dict("records")
    )


def format_context(resp: list[dict]) -> str:
    """
    Format the context response into a human-readable string.

    Parameters
    ----------
    resp : list[dict]
        A list of dictionaries where each dictionary contains information about a title and its associated text chunks.
        Expected keys in each dictionary are 'title', 'url', and 'chunks'.

    Returns
    -------
    str
        A formatted string where each title is followed by its text chunks.
    """
    # Handle empty input
    if not resp:
        return "No context found."

    # Initialize an empty list to store the formatted strings
    output_lines: list[str] = []

    # Get the overlap of text chunks from the RAG config
    overlap: int = get_rag_config()["embeddings"]["overlap"]

    # Iterate through each row in the grouped_df
    for i, row in enumerate(resp):
        # Retrieve title and URL, with fallback for missing values
        title: str = row.get("title", "Unknown Title")
        url: str = row.get("url", "URL not available")

        # Create a header for the title
        output_lines.append(f"{i + 1}. Title '{title}' (URL: {url}):")

        # Handle missing or empty chunks
        chunks: list[str] = row.get("chunks", [])
        rank_abs: list[int] = row.get("rank_abs", [])
        if not chunks:
            output_lines.append("\t- No chunks available.")
        else:
            # Initialize the previous rank (ensure that `r_current - r_before > 1` for the 1st iteration)
            previous_rank: int = -1

            # Add each text chunk under the header
            for r_current, chunk in zip(rank_abs, chunks):
                # if chunks are not consecutive, add current chunk with overlap on the next line
                if r_current - previous_rank > 1:
                    output_lines.append(f"\t- {chunk}")
                elif len(chunk) > overlap:
                    # if chunks are consecutive, add current chunk without overlap to the same line of the previous
                    output_lines[-1] += chunk[overlap:]
                previous_rank = r_current

    # Join all lines into a single string with newline characters
    return "\n".join(output_lines)


def enrich_text_chunks(k_base: Table, chunks_of_title: dict[str, Any], window_size: int = 1) -> dict[str, Any]:
    """
    Sentence-window retrieval: Fetch text chunks before and after the current chunks for a given title and
    return a new dictionary with the enriched 'chunks' and 'rank_abs'. Other keys in the original dictionary
    will be preserved in the new dictionary.

    Parameters
    ----------
    chunks_of_title : dict[str, Any]
        A dictionary containing the following keys:
        - 'hash_title' (str): A hash representing the title of the text.
        - 'rank_abs' (list[int]): The absolute ranks of the text chunks.
        - 'chunks' (list[str]): The text chunks themselves.
        Other keys can also be present, which will be copied to the new dictionary.

    window_size : int, optional
        The number of chunks to fetch before and after the current chunk, covering
        a range of steps. For example, if window_size = 2, it will fetch chunks at
        rank_abs ± 1 and rank_abs ± 2. Must be positive. Default is 1.

    Returns
    -------
    dict[str, Any]
        A new dictionary with all original keys and enriched 'chunks' and 'rank_abs' fields.

    Notes
    -----
    If no new chunks are found, the function returns a dictionary containing only the original chunks.
    """
    # Original ranks for the given title
    original_ranks: list[int] = chunks_of_title["rank_abs"]

    # Generate ranks for chunks within the step range {r ± 1, 2, ..., window_size}
    new_ranks: set[int] = set()
    for r in original_ranks:
        for step in range(1, window_size + 1):
            new_ranks.add(r - step)
            new_ranks.add(r + step)
    # Exclude the original ranks from the new set of ranks
    new_ranks.difference_update(original_ranks)

    # If no new ranks are found, return the original dictionary
    if not new_ranks:
        return chunks_of_title

    # Hash of the title for easy lookup of additional chunks from the knowledge base
    hash_title: str = chunks_of_title["hash_title"]

    # Construct the query to fetch additional chunks from the knowledge base
    new_ranks_str: str = ",".join(map(str, sorted(new_ranks)))
    query_text: str = f"hash_title = '{hash_title}' AND rank_abs IN ({new_ranks_str})"

    # Retrieve additional text chunks from the knowledge base
    fields: list[str] = ["rank_abs", "text", "n_docs"]
    new_chunks: pd.DataFrame = k_base.search().where(query_text).to_pandas()[fields]

    # If no new chunks are found, return the original dictionary
    if new_chunks.empty:
        return chunks_of_title

    # Create a dictionary mapping original ranks to their respective text chunks
    text_dict: dict[int, str] = dict(zip(original_ranks, chunks_of_title["chunks"]))
    # Update it with the retrieved text chunks
    text_dict.update({c["rank_abs"]: c["text"] for c in new_chunks.to_dict("records")})

    # Update the new dictionary with the enriched ranks and chunks
    enriched_chunk_info: dict[str, Any] = chunks_of_title.copy()
    updated_ranks: list[int] = sorted(text_dict)  # sorts by `rank_abs`
    enriched_chunk_info["rank_abs"] = updated_ranks
    enriched_chunk_info["chunks"] = [text_dict[r] for r in updated_ranks]
    enriched_chunk_info["enriched"] = True
    if "n_chunks" in enriched_chunk_info:
        enriched_chunk_info["n_chunks"] = len(updated_ranks)
    if "rank_rel" in enriched_chunk_info:
        enriched_chunk_info["rank_rel"] = (np.array(updated_ranks) / new_chunks["n_docs"].iloc[0]).tolist()
    if "cum_count" in enriched_chunk_info:
        enriched_chunk_info["cum_count"] += len(new_chunks)

    # Return the enriched dictionary
    return enriched_chunk_info


def get_context(
    k_base: Table, query_text: str, n_titles: int = 5, n_retrieve: int = 10, enrich_first: bool = False, **kwargs
) -> str:
    """
    Retrieve, enrich, and format context based on the query text.

    Parameters
    ----------
    k_base : Table
        The knowledge base or table where the context is retrieved from.
    query_text : str
        The search query used to retrieve context from the knowledge base.
    n_retrieve : int, optional
        The number of relevant text chunks to retrieve. Default is 10.
    n_titles : int, optional
        The number of top titles returned after grouping retrieved text chunks by title and sorting by their
        cumulative relevance score. Default is 5.
    enrich_first : bool, optional
        If True, enriches the 1st title in the reordered list of context. Default is False.
    **kwargs : dict
        Additional keyword arguments passed to the `retrieve_context` function.

    Returns
    -------
    str
        A formatted string representing the context based on the query.

    Notes
    -----
    This function retrieves context from the knowledge base, optionally enriches the first
    retrieved title, and formats the result into a readable string.

    If `enrich_first` is set to True, the first title in the reordered list is enriched using
    the `enrich_text_chunks` function.
    """

    # Retrieve raw context
    cxt_raw: list[dict] = retrieve_context(k_base=k_base, query_text=query_text, n_retrieve=n_retrieve, **kwargs)

    # Group retrieved text chunks by title and return to the top `n_titles` titles
    cxt_grouped: list[dict] = group_chunks_by_title(cxt_raw, n_titles=n_titles)

    # Enrich the 1st title with additional text chunks, if `enrich_first` is set to True
    if enrich_first and cxt_grouped:
        cxt_grouped[0] = enrich_text_chunks(k_base=k_base, chunks_of_title=cxt_grouped[0])

    # Format the context into a human-readable string.
    cxt_string: str = format_context(cxt_grouped)

    return cxt_string
