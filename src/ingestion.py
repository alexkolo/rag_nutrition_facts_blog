import json
import warnings
from pathlib import Path
from typing import Any, cast

import lancedb
from lancedb.db import DBConnection
from lancedb.embeddings import SentenceTransformerEmbeddings, get_registry
from lancedb.pydantic import LanceModel, Vector
from lancedb.table import Table
from tqdm import tqdm

from chunking import split_and_filter_paragraphs
from embeddings import EmbeddingFunction

# to ignore FutureWarning from `transformers/tokenization_utils_base.py`
warnings.simplefilter(action="ignore", category=FutureWarning)


def create_lancedb_data_model_simple(
    n_dim_vec: int, lancedb_emb_model: SentenceTransformerEmbeddings | None = None
) -> LanceModel:
    if lancedb_emb_model is None:

        class DataModel(LanceModel):
            vector: Vector(n_dim_vec)  # type: ignore
            text: str
            title: str
            url: str
            tags: str
    else:
        emb_model = cast(SentenceTransformerEmbeddings, lancedb_emb_model)  # to get typing correct

        class DataModel(LanceModel):
            vector: Vector(n_dim_vec) = emb_model.VectorField()  # type: ignore
            text: str = emb_model.SourceField()
            title: str
            url: str
            tags: str

    return DataModel


def extract_metadata(doc: dict[str, Any]) -> dict[str, str]:
    title: str = doc["title"]
    url: str = doc["url"]
    # Tags
    raw_tag_list: list[str] = doc["raw_tags"]
    blog_tag_list: list[str] = [
        tag.split("-", maxsplit=1)[1].replace("-", " ") for tag in raw_tag_list if tag.startswith("tag-")
    ]
    tags: str = ", ".join(sorted(set(blog_tag_list)))  # remove duplicates & join list with space

    return {"title": title, "url": url, "tags": tags}


def generate_table_entries(
    text_chunks: list[str], metadata: dict[str, str], emb_manual: bool, emb_func
) -> list[dict[str, str | list[float]]]:
    if emb_manual:
        # embed text manually
        vectors: list[list[float]] = emb_func(text_chunks)
        return [{"vector": vector, "text": chunk, **metadata} for vector, chunk in zip(vectors, text_chunks)]

    # embedding is done automatically during ingestion
    return [{"text": chunk, **metadata} for chunk in text_chunks]


def lancedb_ingestion_setup(
    lancedb_uri: Path,
    emb_config: dict[str, Any],
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

    # Embedding model Configuration
    emb_model_name: str = emb_config["model_name"]
    n_dim_vec: int = emb_config["n_dim_vec"]
    device = emb_config.get("device", "cpu")

    # 1. create/connect to the database
    print("1/5 Connecting to lancedb database")
    db: DBConnection = lancedb.connect(uri=lancedb_uri)

    # Define the embedding method
    print("2/5 Loading embedding model")
    lancedb_emb_model: SentenceTransformerEmbeddings = (
        get_registry().get("sentence-transformers").create(name=emb_model_name, device=device)
    )
    emb_func: EmbeddingFunction = lancedb_emb_model.generate_embeddings

    # Define data structure
    print("3/5 Defining data structure for table")
    DataModel: LanceModel = create_lancedb_data_model_simple(
        n_dim_vec=n_dim_vec,
        lancedb_emb_model=lancedb_emb_model if not emb_manual else None,
    )
    # show structure
    # print(json.dumps(DataModel.model_json_schema(), indent=2))

    # create table via schema
    print(f"4/5 Creating table: '{table_name}'")
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

    # LanceDB Ingestion setup
    # 1. create/connect to the database
    # 2. Define the embedding method
    # 3. Define data structure
    # 4. create table via schema
    table, emb_func = lancedb_ingestion_setup(
        lancedb_uri=lancedb_uri,
        emb_config=emb_config,
        table_name=table_name,
        emb_manual=emb_manual,
        mode=mode,
    )

    # Ingestion
    print(f"5/5 Ingesting the content of {n_files} files:")
    n_rows: int = 0
    empty_files: list[str] = []
    pbar = tqdm(file_list[0:n_files])
    for json_file in pbar:
        pbar.set_description(json_file.name[:40])

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
            metadata=extract_metadata(doc),  # (same for all chunks)
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
    from constants import LANCEDB_URI, POST_JSON_PATH, get_rag_config

    # get embedding model name
    emb_model_name: str = get_rag_config()["embeddings"]["model_name"]
    print(f"Using embedding model: {emb_model_name}")

    # variable parameters
    n_files: int = 100  # use `None` to process all files
    # time per file: ~0.4 sec
    table_name: str = "table_simple03"
    do_ingestion: bool = True

    # ingestion with simple method
    if do_ingestion:
        print("\nIngestion pipeline started.")
        table: Table = lancedb_ingestion_simple(
            file_list=list(POST_JSON_PATH.glob("*.json")),
            lancedb_uri=LANCEDB_URI,
            emb_config=get_rag_config()["embeddings"],
            n_files=n_files,
            table_name=table_name,
            emb_manual=False,
        )

        """
        Info on last Ingestion, as of 29.08/2024
        - 14547 text chunks of 1281 files have been added.
        - 1 empty files: ['treating-reflux-in-kids-with-diet.json']
        - emb_manual=False (The database takes care the embeddings)
            - name : "table_simple01"
            - time: 11:36<00:00,  1.84it/s
            - database disk size: ~122 MB (json files only take ~8 MB)
        - emb_manual=True (Embeddings created manually beforehand.)
            - name : "table_simple02"
            - time: 01:22, 15.46it/s
            - database disk size: ~114 MB (json files only take ~8 MB)
        """

    # Testing
    db: DBConnection = lancedb.connect(uri=LANCEDB_URI)
    print(f"\n\nList of all tables in the LanceDB database:\n\t{db.table_names()}")

    tbl: Table = db.open_table(table_name)
    print(f"Number of entries in the table '{table_name}': {tbl.count_rows()}")
    print(f"\nShowing first 2 entries of table '{table_name}':")
    print(tbl.head(2))
