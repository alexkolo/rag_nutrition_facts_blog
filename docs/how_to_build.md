
# How I build this bot

## Data Acquisition

- All blog posts from [https://nutritionfacts.org/blog/](https://nutritionfacts.org/blog/) were collected (as of 28.08.2024)
- Notebook: `notebooks/web_scraping.ipynb`
  1. the urls of all blog posts were collected : `data/blog_posts/blog_posts_urls.csv`
      - Number of unique blog post urls: 1281
  2. Then I saved the content of each blog post a json file in `data/blog_posts/json/` with the following structure:
      - url: str
      - title: str
      - created : datatime str
      - updated : datatime str (last update of the blog post)
      - category : list[str] (derived from `raw_tags`)
      - blog_tags : list[str] (derived from `raw_tags`)
      - raw_tags : list[str]
      - paragraphs : list[str] (all paragraphs of the blog post)
        - Since paragraphs were kept separate, the text is already chunked.
      - key_takeaways : list[str] (not all posts have it)

## Data Ingestion: create Knowledge Base

- the data is stored in a local database via `lancedb`
- the script `src/ingestion.py` is used:
  1. set `do_ingestion` to `True` in script and save changes
  2. run: `venv/bin/python -m src.ingestion`
      - takes ~ 10-30 min, depending on the configuration

- Info on last Ingestion, as of 29.08.2024
  - duration: 11:36 (1.84it/s)
  - 14547 text chunks of 1281 files have been added.
    - 1 empty file(s): ['treating-reflux-in-kids-with-diet.json']
  - database disk size: ~120 MB (json files only take ~8 MB)

- database entry structure:

  ```python
    class DataModel(LanceModel):
      vector: Vector(n_dim_vec)
      text: str # from paragraphs only
      # meta data (the same for all paragraphs of the same blog post)
      title: str
      url: str
      tags: str
  ```

  - Meta data of chunks: all paragraphs of the same blog post have the same meta data (e.g. url, blog_tags, title)

  - TODO: add datetime information

- Embedding model:
  - it's defined in the configuration file `./rag_config.toml`
  - At moment, `multi-qa-MiniLM-L6-cos-v1` is used, as it was "tuned for semantic search: Given a query/question, it can find relevant passages. It was trained on a large and diverse set of (question, answer) pairs." [Source](https://www.sbert.net/docs/sentence_transformer/pretrained_models.html)
  - LanceDB has the possible take care of embedding in the background when entries are added to the table , i.e. one does not need to do it before ingestion. But it's much slower than doing the embedding manually before ingestion (see `src/ingestion.py`). [Source](https://lancedb.github.io/lancedb/embeddings/embedding_functions/)
    - This is automatic embedding is needed for using hybrid searches. [Source](https://lancedb.github.io/lancedb/hybrid_search/hybrid_search/)

## IR : Information Retrieval

- testing different indexes
  - pure vector index
  - pure text index
  - hybrid index

- TODO: evaluation

## Create Q&A bot

- create command line interface (CLI) for the bot (for testing purposes)
- create streamlit app for the bot

## Evaluation

### Retrieval Quality

TODO

### Bot Quality

TODO

## Improvements
