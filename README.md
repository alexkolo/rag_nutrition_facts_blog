# Q&A bot about healthy eating & lifestyle habits

This is a bot intended to help answer questions around a healthy eating and lifestyle habits.

It based on [Dr. Greger's Blog Posts on nutritionfacts.org](https://nutritionfacts.org/blog/) (spanning over ~13 years), which are usually well researched and facts-based.

## Problem statement

TODO: expand it

## Run the bot

### In the cloud

- got to the streamlit [app here](https://dr-greger-blog-bot.streamlit.app/)

### In docker

TOOD

### Locally

- clone this repository: `git clone https://github.com/alexkolo/rag_nutrition_facts_blog`

- get right Python version
  - it was build with version `3.12.3`
  - setup suggestions using `pyenv`:

    ```bash
    pyenv install 3.12.x
    pyenv global 3.12.x
    ```

    - [install `pyenv` on Linux or MacOS](https://github.com/pyenv/pyenv)
    - [install `pyenv` on Windows](https://github.com/pyenv-win/pyenv-win)

- setup "User Environment"

  ```bash
  # assumes Python version 3.12.x
  python -m venv venv  # removed via: sudo rm -rf venv
  source venv/bin/activate # for Linux or MacOS
  # for Windows: >.\venv\Scripts\Activate
  bash setup.sh # for Linux or MacOS
  # for Windows:
  # > Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
  # > .\setup.ps1
  ```

## Help improve the bot

- setup "Developer Environment"
  - `pip install --no-cache-dir -e .[dev]`
  - (optional) pre-commit setup: `pre-commit install` (update: `pre-commit autoupdate`)
    - test: `pre-commit run --all-files`

## Docs

- [How I build this bot](docs/how_to_build.md)

## Technologies

- Web Scraping: [Beautiful Soup Library](https://www.crummy.com/software/BeautifulSoup/)

- Text embeddings: pre-trained model [`multi-qa-MiniLM-L6-cos-v1`](https://huggingface.co/sentence-transformers/multi-qa-MiniLM-L6-cos-v1) of the [Sentence Transformers Library](https://www.sbert.net/index.html)
  - build with [PyTorch](https://pytorch.org/get-started/locally/) and [Huggingface](https://huggingface.co/)'s [Transformers Library](https://github.com/huggingface/transformers)
  - It was "tuned for semantic search: Given a query/question, it can find relevant passages. It was trained on a large and diverse set of (question, answer) pairs."

- Vector Store (aka Knowledge Base of RAG): [LanceDB Library](https://lancedb.github.io/lancedb/)

- Information Retrieval (IR):
  - Full-text search (aka Keyword-Search): [Tantivy Library](https://github.com/quickwit-oss/tantivy) (based on BM25) ([LanceDB Doc](https://lancedb.github.io/lancedb/fts/)).
  - Vector Search Metric: Cosine Similarity ([LanceDB Doc](https://lancedb.github.io/lancedb/search/)).
  - Reranker: TBA ([LanceDB Doc](https://lancedb.github.io/lancedb/reranking/)).

- LLM API: [Groq Cloud](https://groq.com/) (free tier)
  - [List of Groq's Models](https://console.groq.com/docs/models)

- Web App: [Streamlit Library](https://streamlit.io/)
- Deployment: [Streamlit Cloud](https://streamlit.io/cloud) (free tier)
