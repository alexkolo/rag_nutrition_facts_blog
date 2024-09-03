# Q&A Chatbot about healthy eating & lifestyle habits

This is a chatbot intended to help answer questions around a healthy eating and lifestyle habits.

It based on [Dr. Greger's Blog Posts on nutritionfacts.org](https://nutritionfacts.org/blog/) (spanning over ~13 years), which are usually well researched and facts-based.

Test it in this [web app](https://dr-greger-blog-bot.streamlit.app/).

## Problem statement

TODO: expand it

## Docs

- [Problem Statement: What problem helps my project solves?](docs/project_description.md)
- [How I build this chatbot](docs/how_to_build.md)
- [Internal project evaluation](docs/project_evaluation_internal.md)

## Use the chatbot

### In the cloud

- got to the streamlit app [here](https://dr-greger-blog-bot.streamlit.app/)

### Run it on your own

- add your [Groq API key](https://console.groq.com/keys) in `.streamlit/secrets.toml` as `GROQ_TOKEN = "..."`

#### Using docker

- ensure docker exists: `docker version`
- ensure docker compose exists: `docker compose version`, if not then [install it](https://docs.docker.com/compose/install/linux/)

- using a Dockerfile:
  - start mongodb server: `docker-compose --file docker-mongodb.yml up -d`
  - build app container: `docker build -t app:latest .`
  - run app container: `docker run -p 8501:8501 app:latest`
  - view it in the browser via this url: <http://localhost:8501>

- using Docker Compose:
  - build & run container: `docker compose up --build`
  - view it in the browser via this url: <http://localhost:8501>
  - stop it: `docker compose down`

#### Using the source code

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

- setup "User Environment":
  - for Linux or MacOS:

    ```bash
    # assumes Python version 3.12.x
    python -m venv venv  # removed via: sudo rm -rf venv
    source venv/bin/activate
    bash setup.sh
    ```

  - for Windows:

    ```powershell
    # assumes Python version 3.12.x
    python -m venv venv
    .\venv\Scripts\Activate
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
    .\setup.ps1
    ```

- start server for the user database: `docker-compose --file docker-mongodb.yml up -d`
- start the app via `streamlit run app.py`
- view it in the browser via this url: <http://localhost:8501>

## Help improve the bot

- setup "Developer Environment"
  - `pip install --no-cache-dir -e .[dev]`
  - pre-commit setup: `pre-commit install`
    - test: `pre-commit run --all-files`

## Technologies

This chatbot was build with the following technologies:

- Web Scraping: [Beautiful Soup Library](https://www.crummy.com/software/BeautifulSoup/)

- Text embeddings: pre-trained model [`multi-qa-MiniLM-L6-cos-v1`](https://huggingface.co/sentence-transformers/multi-qa-MiniLM-L6-cos-v1) of the [Sentence Transformers Library](https://www.sbert.net/index.html)
  - build with [PyTorch](https://pytorch.org/get-started/locally/) and [Huggingface](https://huggingface.co/)'s [Transformers Library](https://github.com/huggingface/transformers)
  - It was "tuned for semantic search: Given a query/question, it can find relevant passages. It was trained on a large and diverse set of (question, answer) pairs."

- Vector Store (aka Knowledge Base of RAG): [LanceDB Library](https://lancedb.github.io/lancedb/)

- Information Retrieval (IR):
  - Full-text search (aka Keyword-Search): [Tantivy Library](https://github.com/quickwit-oss/tantivy) (based on BM25) ([LanceDB Doc](https://lancedb.github.io/lancedb/fts/)).
  - Vector Search (aka Search for nearest neighbors) Metric: Cosine Similarity ([LanceDB Doc](https://lancedb.github.io/lancedb/search/)).
  - Reranker: Linear Combination Reranker with 30% for Vector Search ([LanceDB Doc](https://lancedb.github.io/lancedb/reranking/linear_combination/)).

- LLM API: [Groq Cloud](https://groq.com/) (free tier)
  - [List of Groq's Models](https://console.groq.com/docs/models)

- Web App: [Streamlit Library](https://streamlit.io/)
- Deployment: [Streamlit Cloud](https://streamlit.io/cloud) (free tier)

- Database for User Data: [MongoDB](https://www.mongodb.com/)
