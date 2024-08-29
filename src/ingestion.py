import json
import warnings
from pathlib import Path

import lancedb
from lancedb.db import DBConnection
from lancedb.embeddings import SentenceTransformerEmbeddings, get_registry
from lancedb.pydantic import LanceModel, Vector
from lancedb.table import Table
from tqdm import tqdm

# to ignore FutureWarning from `transformers/tokenization_utils_base.py`
warnings.simplefilter(action="ignore", category=FutureWarning)


def lancedb_ingestion_simple(
    file_list: list[Path],
    lancedb_uri: Path,
    emb_model_name: str,
    n_files: int | None = None,
    table_name: str = "table",
    mode: str = "overwrite",
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
    emb_model_name : str
        The name of the embedding model to use for generating vector embeddings.
    n_files : int, optional
        The maximum number of files to process, by default `None` (all files).
    table_name : str, optional
        The name of the table to create in the database, by default "table".
    mode : str, optional
        The mode to use when creating the table, by default "overwrite".

    Returns
    -------
    Table
        The table object after data has been added.
    """

    # 1. create/connect to the database
    print("1/5 Connecting to lancedb database")
    db: DBConnection = lancedb.connect(uri=lancedb_uri)

    # Define the embedding function
    print("2/5 Loading embedding model")
    emb_model: SentenceTransformerEmbeddings = get_registry().get("sentence-transformers").create(name=emb_model_name)
    n_dim_vec = emb_model.ndims()

    # Define data structure
    print("3/5 Defining data structure for table")

    class DataModel(LanceModel):
        vector: Vector(dim=n_dim_vec) = emb_model.VectorField()
        text: str = emb_model.SourceField()
        title: str
        url: str
        blog_tags: str

    # show structure
    # print(json.dumps(DataModel.model_json_schema(), indent=2))

    # create table via schema
    print(f"4/5 Creating table: '{table_name}'")
    table: Table = db.create_table(name=table_name, schema=DataModel, mode=mode)

    # Ingestion
    print(f"5/5 Ingesting the content of {n_files} files:")
    n_rows: int = 0
    empty_files: list[str] = []
    pbar = tqdm(file_list[0:n_files])
    for json_file in pbar:
        pbar.set_description(json_file.name[:40])
        with open(json_file) as f:
            doc: dict = json.load(f)
        paragraphs: list[str] = doc["paragraphs"]
        if not paragraphs:
            empty_files.append(json_file.name)
            continue
        title: str = doc["title"]
        url: str = doc["url"]
        blog_tags: str = " ".join(set(doc["blog_tags"]))  # remove duplicates and join with space
        table_rows: list[dict[str, str]] = [
            {"text": para, "title": title, "url": url, "blog_tags": blog_tags} for para in paragraphs
        ]
        n_rows += len(table_rows)

        # add data to the table, which automatically creates embeddings for the text column stored in the vector column
        table.add(data=table_rows)
    # optimize the table for faster reads.
    table.compact_files()

    print(f"Ingestion complete 🚀.  {n_rows} text chunks of {n_files} files have been added.")

    if empty_files:
        print(f"\n{len(empty_files)} empty files:\n{empty_files}\n")

    return table


def lancedb_data_model_simple(emb_model_name: str) -> LanceModel:
    """
    Creates a LanceDB data model based on the specified embedding model of `sentence-transformers`.
    List of Models : https://www.sbert.net/docs/sentence_transformer/pretrained_models.html
    Requires to have installed the `sentence_transformers` package.

    Parameters
    ----------
    emb_model_name : str
        The name of the embedding model to use for generating vector embeddings.

    Returns
    -------
    LanceModel
        A data model class with fields for the vector embedding, text, title, url, and blog_tags.
    """

    # Define the embedding function
    emb_model: SentenceTransformerEmbeddings = get_registry().get("sentence-transformers").create(name=emb_model_name)
    n_dim_vec = emb_model.ndims()

    # Define the data model or schema
    class DataModel(LanceModel):
        vector: Vector(dim=n_dim_vec) = emb_model.VectorField()
        text: str = emb_model.SourceField()
        title: str
        url: str
        blog_tags: str

    return DataModel


if __name__ == "__main__":
    # fixed parameters
    from constants import LANCEDB_URI, post_path_json

    # variable parameters
    n_files: int = None  # use `None` to process all files
    # time per file: ~0.5 sec
    table_name: str = "table_simple01"
    do_ingestion: bool = False

    # ingestion with simple method
    if do_ingestion:
        print("\nIngestion pipeline started.")
        table: Table = lancedb_ingestion_simple(
            file_list=list(post_path_json.glob("*.json")),
            lancedb_uri=LANCEDB_URI,
            emb_model_name="multi-qa-MiniLM-L6-cos-v1",
            n_files=n_files,
            table_name=table_name,
        )

        """
        Info on last Ingestion, as of 29.08/2024
        - time: 11:36<00:00,  1.84it/s
        - 14547 text chunks of 1281 files have been added.
        - 1 empty files: ['treating-reflux-in-kids-with-diet.json']
        - database disk size: ~120 MB (json files only take ~8 MB)
        """

    # Testing
    db: DBConnection = lancedb.connect(uri=LANCEDB_URI)
    print(f"\n\nList of all tables in the LanceDB database:\n{db.table_names()}")

    tbl: Table = db.open_table(table_name)
    print(f"Number of rows in the table '{table_name}': {tbl.count_rows()}")
    print(f"\nShowing first 2 rows of table '{table_name}':")
    print(tbl.head(2))
