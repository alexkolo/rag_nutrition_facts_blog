import hashlib
import json
import warnings
from pathlib import Path
from typing import Any

import lancedb
from lancedb.db import DBConnection
from lancedb.embeddings import get_registry
from lancedb.embeddings.base import TextEmbeddingFunction
from lancedb.pydantic import LanceModel, Vector
from lancedb.table import Table
from tqdm import tqdm

from src.chunking import recursive_text_splitter02, split_and_filter_paragraphs
from src.embeddings import EmbeddingFunction

# to ignore FutureWarning from `transformers/tokenization_utils_base.py`
warnings.simplefilter(action="ignore", category=FutureWarning)

REPLACEMENTS: dict[str, str] = {
    "-": " ",
    ".": " ",
    ",": " ",
    "!": " ",
    "?": " ",
    "'": " ",
    '"': " ",
    "(": " ",
    ")": " ",
    "[": " ",
    "]": " ",
    "\\": " ",
    ":": " ",
    ";": " ",
    "*": " ",
    "&": " ",
    "%": " ",
    "^": " ",
    "~": " ",
    "#": " ",
    "$": " ",
    "@": " ",
    "`": " ",
}


def extract_base_metadata(doc: dict[str, Any]) -> dict[str, str]:
    title: str = doc["title"]
    url: str = doc["url"]
    # Tags
    raw_tag_list: list[str] = doc["raw_tags"]
    blog_tag_list: list[str] = [
        tag.split("-", maxsplit=1)[1].replace("-", " ") for tag in raw_tag_list if tag.startswith("tag-")
    ]
    tags: str = ", ".join(sorted(set(blog_tag_list)))  # remove duplicates & join elements with a space

    return {"title": title, "url": url, "tags": tags}


def generate_table_entries(
    text_chunks: list[str],
    metadata_fixed: dict[str, str],
    emb_manual: bool,
    emb_func,
    metadata_ind: list[dict] | None = None,
) -> list[dict[str, str | list[float]]]:
    if emb_manual:
        # embed text manually
        vectors: list[list[float]] = emb_func(text_chunks)
        return [{"vector": vector, "text": chunk, **metadata_fixed} for vector, chunk in zip(vectors, text_chunks)]

    if metadata_ind is not None:
        return [{"text": chunk, **metadata, **metadata_fixed} for chunk, metadata in zip(text_chunks, metadata_ind)]

    # embedding is done automatically during ingestion
    return [{"text": chunk, **metadata_fixed} for chunk in text_chunks]


def lancedb_ingestion_setup(
    lancedb_uri: Path,
    emb_config: dict[str, Any],
    meta_fields: dict[str, Any],
    emb_manual: bool = False,
    table_name: str = "table",
    mode: str = "overwrite",
) -> tuple[Table, EmbeddingFunction]:
    """
    LanceDB Ingestion setup
    1. create/connect to the database
    2. Define the embedding method
    3. Define data structure
    4. create table via schema

    Parameters
    ----------
    lancedb_uri : Path
        The URI of the LanceDB instance to connect to.
    emb_config : dict
        The configuration for the embedding model and chunking.
    meta_fields : dict[str, Any]
        The metadata fields to include in the table entries.
    emb_manual : bool, optional
        Whether to embed the data before ingesting it into the database, by default False.
        False: The database takes care the embeddings.
        True: Embeddings created manually beforehand.
    table_name : str, optional
        The name of the table to create in the database, by default "table".
    mode : str, optional
        The mode to use when creating the table, by default "overwrite".

    Returns
    -------
    tuple[Table, EmbeddingFunction]
        A tuple of the created table and the embedding function.
    """
    print(f"Ingestion pipeline started for table '{table_name}'.")

    # Embedding model Configuration
    emb_model_provider: str = emb_config["model_provider"]
    emb_model_name: str = emb_config["model_name"]
    n_dim_vec: int = emb_config["n_dim_vec"]
    device = emb_config.get("device", "cpu")

    # 1. create/connect to the database
    print("1. Connecting to lancedb database")
    db: DBConnection = lancedb.connect(uri=lancedb_uri)

    # Define the embedding method
    print("2. Loading embedding model")
    lancedb_emb_model: TextEmbeddingFunction = (
        get_registry().get(emb_model_provider).create(name=emb_model_name, device=device)
    )
    emb_func: EmbeddingFunction = lancedb_emb_model.generate_embeddings

    # Define data structure
    print("3. Defining data structure of table")
    # DataModel: LanceModel = create_lancedb_data_model_simple(
    #     n_dim_vec=n_dim_vec,
    #     lancedb_emb_model=lancedb_emb_model if not emb_manual else None,
    # )
    if emb_manual:

        class BaseDataModel(LanceModel):
            vector: Vector(n_dim_vec)  # type: ignore
            text: str
    else:

        class BaseDataModel(LanceModel):
            vector: Vector(n_dim_vec) = lancedb_emb_model.VectorField()  # type: ignore
            text: str = lancedb_emb_model.SourceField()

    # create a dynamic class that adds fields from `meta_fields` to `BaseDataModel`
    data_model_setup = {"__module__": __name__, "__annotations__": meta_fields}
    DataModel: LanceModel = type("DataModel", (BaseDataModel,), data_model_setup)

    # show structure
    # check fields via `DataModel.model_fields`
    # print(json.dumps(DataModel.model_json_schema(), indent=2))

    # create table via schema
    print("4. Creating table itself")
    table: Table = db.create_table(name=table_name, schema=DataModel, mode=mode)

    return table, emb_func


def lancedb_ingestion_simple(
    file_list: list[Path],
    lancedb_uri: Path,
    emb_config: dict[str, Any],
    emb_manual: bool = False,
    table_name: str = "table",
    mode: str = "overwrite",
    n_files: int | None = None,
) -> Table:
    """
    Simple method pipeline to create and populate a LanceDB table with text data and embeddings.
    The specified embedding model is taken from `sentence-transformers`.
    List of Models : https://www.sbert.net/docs/sentence_transformer/pretrained_models.html
    Requires to have installed the `sentence_transformers` package.

    Parameters
    ----------
    file_list : list[Path]
        A list of paths to JSON files containing the data to be ingested.
    lancedb_uri : Path
        The URI of the LanceDB instance to connect to.
    emb_config : dict
        The configuration for the embedding model and chunking.
    emb_manual : bool, optional
        Whether to embed the data before ingesting it into the database, by default False.
        False: The database takes care the embeddings.
        True: Embeddings created manually beforehand.
    table_name : str, optional
        The name of the table to create in the database, by default "table".
    mode : str, optional
        The mode to use when creating the table, by default "overwrite".
    n_files : int, optional
        The maximum number of files to process, by default `None` (all files).

    Returns
    -------
    Table
        The table object after data has been added.
    """
    # chunking configuration is calibrated to the embedding model
    n_char_max = emb_config.get("n_char_max", 1000)
    overlap = emb_config.get("overlap", 100)

    # Define additional metadata fields
    meta_fields: dict[str, Any] = {"title": str, "url": str, "tags": str}

    # LanceDB Ingestion setup
    # 1. create/connect to the database
    # 2. Define the embedding method
    # 3. Define data structure
    # 4. create table via schema
    table, emb_func = lancedb_ingestion_setup(
        lancedb_uri=lancedb_uri,
        emb_config=emb_config,
        meta_fields=meta_fields,
        table_name=table_name,
        emb_manual=emb_manual,
        mode=mode,
    )

    # Ingestion
    print(f"5. Ingesting the content of {n_files or len(file_list)} files:")
    n_rows: int = 0
    empty_files: list[str] = []
    pbar = tqdm(file_list[0:n_files])
    for json_file in pbar:
        pbar.set_description(f"{json_file.name[:40]:<40}")

        # load data
        with open(json_file, encoding="utf-8") as f:
            doc: dict[str, Any] = json.load(f)

        # extract data
        text_chunks: list[str] = doc["paragraphs"]

        # ignore files without any text
        if not text_chunks:
            empty_files.append(json_file.name)
            continue

        # split paragraphs if necessary and remove paragraphs that only contain questions
        text_chunks = split_and_filter_paragraphs(text_chunks, n_char_max=n_char_max, overlap=overlap)

        # convert data into table entries
        table_entries: list[dict[str, str | list[float]]] = generate_table_entries(
            text_chunks=text_chunks,
            metadata_fixed=extract_base_metadata(doc),  # (same for all chunks)
            emb_manual=emb_manual,
            emb_func=emb_func,
        )

        # add data to the table
        table.add(data=table_entries)
        n_rows += len(table_entries)

    # optimize the table for faster reads.
    table.compact_files()

    print(f"Ingestion complete 🚀.  {n_rows} text chunks of {n_files or len(file_list)} files have been added.")

    if empty_files:
        print(f"\n{len(empty_files)} empty files:\n{empty_files}\n")

    return table


def lancedb_ingestion_full_text(
    file_list: list[Path],
    lancedb_uri: Path,
    emb_config: dict[str, Any],
    emb_manual: bool = False,
    table_name: str = "table",
    mode: str = "overwrite",
    n_files: int | None = None,
) -> Table:
    # Define additional metadata fields
    meta_fields: dict[str, Any] = {"title": str, "url": str, "tags": str, "full_text": str}

    # LanceDB Ingestion setup
    # 1. create/connect to the database
    # 2. Define the embedding method
    # 3. Define data structure
    # 4. create table via schema
    table, emb_func = lancedb_ingestion_setup(
        lancedb_uri=lancedb_uri,
        emb_config=emb_config,
        meta_fields=meta_fields,
        table_name=table_name,
        emb_manual=emb_manual,
        mode=mode,
    )

    # Ingestion
    print(f"5/5 Ingesting the content of {n_files or len(file_list)} files:")
    n_rows: int = 0
    empty_files: list[str] = []
    pbar = tqdm(file_list[0:n_files])
    for json_file in pbar:
        pbar.set_description(json_file.name[:40])

        # load data
        with open(json_file, encoding="utf-8") as f:
            doc: dict[str, Any] = json.load(f)

        # extract data
        paragraphs: list[str] = doc["paragraphs"]

        # ignore files without any text
        if not paragraphs:
            empty_files.append(json_file.name)
            continue

        # meta data
        metadata: dict[str, str] = extract_base_metadata(doc)

        # join all paragraphs into one
        metadata["full_text"] = " ".join(paragraphs)

        # title + tags used also for vector search
        text_chunks: list[str] = [metadata["title"] + " - " + metadata["tags"]]

        # convert data into table entries
        table_entries: list[dict[str, str | list[float]]] = generate_table_entries(
            text_chunks=text_chunks,
            metadata_fixed=metadata,
            emb_manual=emb_manual,
            emb_func=emb_func,
        )

        # add data to the table
        table.add(data=table_entries)
        n_rows += len(table_entries)

    # optimize the table for faster reads.
    table.compact_files()

    print(f"Ingestion complete 🚀.  {n_rows} text chunks of {n_files or len(file_list)} files have been added.")

    if empty_files:
        print(f"\n{len(empty_files)} empty files:\n{empty_files}\n")

    return table


def create_hash_of_str(text: str, n_char: int = 12) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:n_char]


def lancedb_ingestion_meta(
    file_list: list[Path],
    lancedb_uri: Path,
    emb_config: dict[str, Any],
    emb_manual: bool = False,
    table_name: str = "table",
    mode: str = "overwrite",
    n_files: int | None = None,
) -> Table:
    # chunking configuration is calibrated to the embedding model
    n_char_max = emb_config.get("n_char_max", 1000)
    overlap = emb_config.get("overlap", 100)

    # Define additional metadata fields
    meta_fields: dict[str, Any] = {
        # Meta Data of the text chunk of a blog post
        "hash_doc": str,  # Unique ID of text chunk (as a hash of url + title + text)
        "rank": int,  # Rank of the text chunk in the blog post
        "tags_doc": str,  # Tags of "tags_all" that exists in the text chunk
        "n_tags_doc": int,  # Number of matching tags in the text chunk
        "n_words_doc": int,  # Number of words in the text chunk
        "n_char_doc": int,  # Number of characters in the text chunk
        # Meta Data of the blog post (same value for its all text chunks)
        "title": str,  # Title of blog post
        "url": str,  # URL of blog post
        "tags_all": str,  # Tags of blog post
        "hash_title": str,  # Unique ID of blog post (as a hash of the url + title)
    }

    # LanceDB Ingestion setup
    # 1. create/connect to the database
    # 2. Define the embedding method
    # 3. Define data structure
    # 4. create table via schema
    table, emb_func = lancedb_ingestion_setup(
        lancedb_uri=lancedb_uri,
        emb_config=emb_config,
        meta_fields=meta_fields,
        table_name=table_name,
        emb_manual=emb_manual,
        mode=mode,
    )

    # Ingestion
    print(f"5. Ingesting the content of {n_files or len(file_list)} files:")
    n_rows: int = 0
    empty_files: list[str] = []
    pbar = tqdm(file_list[0:n_files])
    for json_file in pbar:
        pbar.set_description(f"{json_file.name[:40]:<40}")

        # load data
        with open(json_file, encoding="utf-8") as f:
            doc: dict[str, Any] = json.load(f)

        # extract data
        raw_chunks: list[str] = doc["paragraphs"]

        # ignore files without any text
        if not raw_chunks:
            empty_files.append(json_file.name)
            continue

        # split paragraphs if necessary and remove paragraphs that only contain questions
        full_text: str = " ".join(raw_chunks)
        even_chunks: list[str] = recursive_text_splitter02(text=full_text, n_char_max=n_char_max, overlap=overlap)

        # Fixed Meta Data (same for all chunks)
        metadata_fixed: dict[str, str] = {"title": doc["title"], "url": doc["url"]}
        hash_title_src: str = f"{metadata_fixed['url']}-{metadata_fixed['title']}"
        metadata_fixed["hash_title"] = create_hash_of_str(hash_title_src)

        # get set of tags
        raw_tags: list[str] = doc["raw_tags"]
        tags_set: set[str] = {
                tag
                for tag_str in raw_tags
                if tag_str.startswith("tag-")
                for tag in tag_str.split("-")[1:]
                if len(tag) > 3
        }
        metadata_fixed["tags_all"] = " ".join(sorted(tags_set))

        # Individual Meta Data (different for each chunk)
        metadata_ind: list[dict[str, Any]] = []
        for rank, chunk in enumerate(even_chunks):
            word_list: list[str] = chunk.lower().translate(str.maketrans(REPLACEMENTS)).split()
            # Tags of "tags_all" that exists in the text chunk
            tags_doc: set[str] = set(word_list) & tags_set
            metadata_ind.append(
                {
                    "rank": rank,
                    "hash_doc": create_hash_of_str(f"{hash_title_src}-{chunk:20}"),
                    "tags_doc": " ".join(sorted(tags_doc)),
                    "n_tags_doc": len(tags_doc),
                    "n_words_doc": len(word_list),
                    "n_char_doc": len(chunk),
                }
            )

        # convert data into table entries
        table_entries: list[dict[str, str | list[float]]] = generate_table_entries(
            text_chunks=raw_chunks,
            metadata_fixed=metadata_fixed,
            metadata_ind=metadata_ind,
            emb_manual=emb_manual,
            emb_func=emb_func,
        )

        # add data to the table
        table.add(data=table_entries)
        n_rows += len(table_entries)

    # optimize the table for faster reads.
    table.compact_files()

    print(f"Ingestion complete 🚀.  {n_rows} text chunks of {n_files or len(file_list)} files have been added.")

    if empty_files:
        print(f"\n{len(empty_files)} empty files:\n{empty_files}\n")

    return table


if __name__ == "__main__":
    print("Script started.")

    # fixed parameters
    from src.constants import LANCEDB_URI, POST_JSON_PATH, get_rag_config

    # variable parameters
    n_files: int | None = None  # use `None` to process all files

    # Ingestion pipeline config
    ing_pipe_config: dict[str, Any] = {
        "file_list": list(POST_JSON_PATH.glob("*.json")),
        "lancedb_uri": LANCEDB_URI,
        "emb_config": get_rag_config()["embeddings"],
        "n_files": n_files,
    }

    # ingestion with simple method
    table_name: str = "table_simple03"
    if False:
        table: Table = lancedb_ingestion_simple(
            table_name=table_name,
            emb_manual=False,
            **ing_pipe_config,
        )

        """
        Info on last Ingestions
        - 1281 files
        - 1 empty files: ['treating-reflux-in-kids-with-diet.json']
        - "table_simple01" as of 29.08.2024
            - emb_manual=False
            - time: 11:36  1.84it/s
            - 14547 text chunks
            - database disk size: ~122 MB (json files only take ~8 MB)
        - "table_simple02" as of 29.08.2024
            - emb_manual=True
            - time: 01:22, 15.46it/s
            - 14547 text chunks
            - database disk size: ~114 MB (json files only take ~8 MB)
        - "table_simple03" as of 30.08.2024
            - emb_manual=False
            - time: 31:14  1.46s/it
            - 13957 text chunks
            - database disk size: ~123 MB (json files only take ~8 MB)
        """

    # ingestion for full text posts
    if False:
        table_name: str = "fulltext01"
        table: Table = lancedb_ingestion_full_text(
            table_name=table_name,
            emb_manual=False,
            **ing_pipe_config,
        )

        """
        Info on last Ingestion, as of 29.08/2024
        - 1 empty files: ['treating-reflux-in-kids-with-diet.json']
        - "fulltext01"
            - emb_manual=False
            - time: 24:02 (1.13s/it)
            - 1280 text chunks
            - database disk size: ~69 MB (json files only take ~8 MB)
        """

    # ingestion for full text posts
    if True:
        table_name: str = "table_simple04"
        table: Table = lancedb_ingestion_meta(
            table_name=table_name,
            emb_manual=False,
            **ing_pipe_config,
        )

    # Testing
    db: DBConnection = lancedb.connect(uri=LANCEDB_URI)
    print(f"\n\nList of all tables in the LanceDB database:\n\t{db.table_names()}")

    tbl: Table = db.open_table(table_name)
    print(f"Number of entries in the table '{table_name}': {tbl.count_rows()}")
    print(f"\nShowing first 2 entries of table '{table_name}':")
    print(tbl.head(2))

    print("\nScript finished.")
