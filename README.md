# Nutrition Insights with Dr. Greger's Digital Twin 🥦 (a RAG-based Q&A chatbot)

This digital assistant, inspired by [Dr. Michael Greger & his team](https://nutritionfacts.org/team/) at [NutritionFacts.org](https://nutritionfacts.org/about/), was created to answer user questions about healthy eating and lifestyle choices. Drawing from [over 1,200 well-researched blog posts since 2011](https://nutritionfacts.org/blog/), it provides science-backed insights to help users live a healthier, more informed life.

Start chatting with Dr. Greger's Digital Twin [here](https://dr-greger-blog-bot.streamlit.app/).

## Problem statement

- [What kind of problems does this digital assistant help mitigate?](docs/project_description.md)

## Dataset (aka RAG knowledge base)

The raw data used to build the RAG knowledge base is stored in `data/blog_posts/json`. It consists of all blog posts from [https://nutritionfacts.org/blog/](https://nutritionfacts.org/blog/) (as of 28.08.2024). See the `notebooks/web_scraping.ipynb` notebook for more technical details on the web scraping process.

The data was automatically ingested into a vector store located in `databases/my_lancedb/` using the [LanceDB Library](https://lancedb.github.io/lancedb/) and the Python script `src/ingestion.py`.

## Information Retrieval (IR)

To take advantage of the vector search, the text was embedded using the pre-trained model [`multi-qa-MiniLM-L6-cos-v1`](https://huggingface.co/sentence-transformers/multi-qa-MiniLM-L6-cos-v1) from the [Sentence Transformers Library](https://www.sbert.net/index.html), as it is tuned for Q&A chatbots.

{TOOD: Add description here}

### Improving Ideas

- if similar blog post title (cosine similarity > 0.9), take the more recent one (unless the from the save year)
- also provider the chunk before and after the retrieve chunk from the same blog post

## Evaluation

{TOOD: Add description here}

## Use the chatbot

### In the cloud (aka deployed)

- got to the streamlit app [here](https://dr-greger-blog-bot.streamlit.app/).
- the corresponding dashboard for monitoring the app usage is [here](https://chatbotdrgreger.grafana.net/public-dashboards/1ae4a1c3c47c41478e16d97aaa5a2276).

    > [!IMPORTANT]
    > The online dashboard will stop working properly (aka won't show any data) on 18.09.2024 due to the 14-day trial period ending by Grafana. 😭
  - I'm using a MongoDB plugin that is only available for the Enterprise version of Grafana. Unfortunately, I found this out only after setting up my own MongoDB and creating the dashboard. 😒
  - I tried to rebuild it using MongoDB's own dashboard tool "Charts". See the result [here](https://charts.mongodb.com/charts-project-0-dwgewmy/public/dashboards/10ed0c93-9fb1-4b89-a1e3-966fddef4f27). However, I was only able to reproduce the simplest panels. Moreover, I couldn't figure out to set up a time filter as in Grafana. 😓

### Run it on your own

- add a [Groq API key](https://console.groq.com/keys) in `.streamlit/secrets.toml` as `GROQ_TOKEN = "..."` (since the app is using [Groq Cloud](https://groq.com/) as my LLM API provider, as it is free tier).

> [!NOTE]
> There is no local dashboard to monitor the app usage, since Grafana doesn't offer the MongoDB data plugin for the free tier. [Source](https://grafana.com/docs/grafana/latest/introduction/grafana-enterprise/#enterprise-data-sources) (see comment above for the deployed version)

#### In a container (using docker)

- ensure docker exists: `docker version`
- ensure docker compose exists: `docker compose version`, if not then [install it](https://docs.docker.com/compose/install/linux/)

- using Docker Compose:
  - build & run containers: `docker compose up --build`
  - view app in the browser via this url: <http://localhost:8501>

- for developers: using the Dockerfile of the app:
  - start server for the user database: `docker-compose --file docker-mongodb.yml up -d`
  - build app container: `docker build -t app:latest .`
  - run app container: `docker run -p 8501:8501 app:latest`
  - view app in the browser via this url: <http://localhost:8501>

#### From the source code

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

The chatbot was build with the following technologies:

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

## Docs

- [Internal log on how I build this chatbot](docs/how_to_build.md)
- [Internal project evaluation](docs/project_evaluation_internal.md)
