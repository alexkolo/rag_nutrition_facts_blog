
# How I build this bot

- As I'm interest in living health and healthy lives and very much the [blog post of Dr. Greger](https://nutritionfacts.org/blog/), I decided to build a bot based on this well researched blog posts.

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

- this work led to the creation of the module `src.web_scraping`

## Data Ingestion: create RAG Knowledge Base

- I decided to use [`LanceDB`](https://lancedb.github.io/lancedb/) as knowledge base, as it's fast and easy to use and does not require a spin up a server in a Docker container. Also it's compatible with [streamlit cloud](https://streamlit.io/cloud), unlike [ChromaDB](https://discuss.streamlit.io/t/issues-with-chromadb-vector-store-when-deploying-to-streamlit-due-to-pysql3-version-in-deployment-environment/77983).

- The notebook `notebooks/data_ingestion.ipynb` was used to test different parts of the ingestion process.

- This work led to the creation of the modules: `src.constants`, `src.embeddings` ,`src.chunking` & `src.ingestion`

### Script

The script `src/ingestion.py` is used for the ingestion of the data:

1. In the script, change `if False:` to `if True:`.
2. To take advantage of hybrid search (recommended), use `emb_manual=False` in the script (default), which means that embeddings are handled by the database.
3. run `venv/bin/python -m src.ingestion` in terminal
    - it takes ~ 10-30 min, depending on the configuration

- Info on last Ingestion, as of 29.08.2024

  ```plaintext
  - duration: 11:36 (1.84it/s)
  - 14547 text chunks of 1281 files have been added.
    - 1 empty file(s): ['treating-reflux-in-kids-with-diet.json']
  - database disk size: ~120 MB (json files only take ~8 MB)
  ```

### Technical Details

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

  - All chunks of the same blog post have the same meta data (e.g. url, blog_tags, title).

- Chunking:
  - Since the paragraphs were kept separate during the web scraping, the blog posts are technically already chunked but this chunking wasn't very useful. Hence, the blog posts were chunked before the ingestion using a recursive text splitter, which the algorithm copied from[here](https://github.com/lancedb/vectordb-recipes/blob/main/tutorials/RAG-from-Scratch/RAG_from_Scratch.ipynb). See `src.chunking.recursive_text_splitter` for technical details.
  - Chunksize and overlap follow the industry standard: 1000 and 100 characters, respectively (~250 and ~25 tokens). This is also in line with the used embedding model, which was trained on 250-token texts.

- Embedding model:
  - it's defined in the configuration file `./rag_config.toml`
  - At moment, `multi-qa-MiniLM-L6-cos-v1` is used, as it was "tuned for semantic search: Given a query/question, it can find relevant passages. It was trained on a large and diverse set of (question, answer) pairs." [Source](https://www.sbert.net/docs/sentence_transformer/pretrained_models.html)
  - LanceDB has the possible take care of embedding in the background when entries are added to the table , i.e. one does not need to do it before ingestion. But it's much slower than doing the embedding manually before ingestion (see `src/ingestion.py`). [Source](https://lancedb.github.io/lancedb/embeddings/embedding_functions/)
    - This is automatic embedding is needed for using hybrid searches. [Source](https://lancedb.github.io/lancedb/hybrid_search/hybrid_search/)

- GitHub Repository Upload:
  - one can upload a filled database to the github repository, but some fixes are necessary:
    - adjust `.gitignore` : commenting out the line `*.manifest` if present.
    - adjust `.pre-commit-config.yaml` : adding `exclude: '\.manifest$'` to the hooks `trailing-whitespace`, `end-of-file-fixer` & `mixed-line-ending`.

## Testing Information Retrieval (IR)

- I experimented with different indexes and search algorithms (vector, full test, hybrid) that [LanceDB supports](https://lancedb.github.io/lancedb/guides/tables/). See the `notebooks/retrieval.ipynb` for more details.
  - During this I found out, that it was necessary to let LanceDB handle the embedding during ingestion in order to use [hybrid search](https://lancedb.github.io/lancedb/hybrid_search/hybrid_search/).

## Full RAG flow

- In the `notebooks/rag_flow.ipynb` I tested the full RAG flow, which lead to creation of the modules: `src/retrieval`, `src.prompt_building` & `src.llm_api`
- The RAG flow was then further tested and refined with the streamlit app (see next section).

## Building the Q&A Bot Web-App

### App Framework

- I use the [Streamlit Library](https://streamlit.io/), given it's fast and easy to use and it can be deployed for free with the [Streamlit Cloud](https://streamlit.io/cloud) (given some constrains).
  - See `app.py` for details
  - Start the app via `streamlit run app.py` in the terminal & view it in browser via this url: `http://localhost:8501`

- Streamlit Issues:
  - if new imports are added to the `app.py`, the app needs to be rebooted.

### App Design Choices

- As LLM API provider, I choose [Groq](https://groq.com), as it is free, fast and sufficient for this use case.
  - It has an interesting collection of recent open-weights LLMs to choose from: [List of Groq's Models](https://console.groq.com/docs/models)
    - The App picks a LLM based on the current active LLMs of Groq and a ranked list of LLMs made by me.
  - TODO:
    - user can provide their own Groq API key to reduce problems with rate limits.
    - user can choose their own LLM.

- I created a chat experience rather than a simple query/response experience since that feels more natural.
  - For this to work, the retrieved context from the last user query is feed into the system message at the beginning of the chat history. Hence, the bot always gets a new system message after each new user query while being also aware of the previous user queries and bot answers for a given chat session and is able take advantage of that. See `src.llm_api.build_full_llm_chat_input` for more details.
  - As a chat history could get too long to be handled as a input to an LLM, the app keeps track of the token length of the chat history and blocks any user query, when it reaches a threshold of the LLM API provider and suggests a reset of the chat history.
  - To keep global token usage low, each user query is limited to 500 characters.

TODO:

- bot avatar
- wake up boot
- welcome message
- disclaimers
- user feedback rating
- ask for name
- database

## Dockerization / Containerization

- I created a minimal Dockerfile following the [official streamlit guide](https://docs.streamlit.io/deploy/tutorials/docker) and this [post](https://stackoverflow.com/questions/73063486/how-to-create-a-dockerfile-for-streamlit-app).
  - I took advantage of `setup.cfg` for the installation of the dependencies
- I used `.dockerignore` to ignore unneeded files and keep the image size small
  - image size: ~2.13GB

- Useful docker commands:
  - After canceling a build, run `docker builder prune` for clean up
  - Checking image size: `docker images` or `docker image ls`
  - Disk usage summary by Docker: `docker system df`
  - get detailed information about a specific image: `docker image inspect <image_id_or_name>`

## Monitoring

### User Database

- I decided to a MongoDB to save user data, as I can get a free online database, which I can use for the deployed app.
- I created the python class `MongodbClient` based on this [documentation](https://www.w3schools.com/python/python_mongodb_getstarted.asp) to interact with MongoDB.

- I create a local MongoDB Server via Docker Compose:
  - Start Server: `docker-compose --file docker-mongodb.yml up`
  - Stop Server: `docker-compose --file docker-mongodb.yml down`
  - add config in `rag_config.toml` :

    ```toml
    [mongodb.local]
    db_name = "rag_user_info"
    coll_name = "chatbot_dr_greger"
    uri = "mongodb://user:password@localhost:27017/admin"

    [mongodb.docker]
    db_name = "rag_user_info"
    coll_name = "chatbot_dr_greger"
    uri = "mongodb://user:password@mongodb:27017/admin"
    ```

  - Apprently, the uri changes, when the server access via

- create remote MongoDB:
  1. create account [here](https://account.mongodb.com/account/login)
  2. create cluster
  3. browse collections
  4. create database & collection: "rag_user_info" and "chatbot_dr_greger" (use cluster index collection)
  5. get "uri": (left menu) "Overview" -> "Application Development" -> "Get connection string" -> "Drivers"
  - add config in `.streamlit/secrets.toml`:

    ```toml
    [mongodb]
    db_name = "rag_user_info"
    coll_name = "chatbot_dr_greger"
    uri = "mongodb+srv://{username}:{password}@{cluster}.mongodb.net/?retryWrites=true&w=majority&appName={app_name}"
    ```

### Dashboard

- dashboard: <https://chatbotdrgreger.grafana.net>
- needed to connect withthe MongoDB, entering the uri as some stage
- query data examples [here](https://grafana.com/docs/plugins/grafana-mongodb-datasource/latest/mongodb-query-editor/)
  - `rag_user_info.chatbot_dr_greger.find({})` # get all entries
  - `rag_user_info.chatbot_dr_greger.aggregate([{ $count: "totalEntries" } ])` # count all entries
  - `rag_user_info.chatbot_dr_greger.find({user_name : "Sam"})` # get all entries for Sam

- published dashboard: [here](https://chatbotdrgreger.grafana.net/public-dashboards/1ae4a1c3c47c41478e16d97aaa5a2276?from=now-24h&to=now&timezone=browser)
  - Go to Dashboard -> "Share" icon in  top-right corner -> Public Dashboard
- export/save dashboard: Settings -> JSON Model -> copy & past
  - see example: `docs/20240903_dashboard.json`
  -

- run locally
  - `sudo chown -R 472:472 ./databases/grafana`
  - Start Server: `docker-compose --env-file=docker.env -f docker-grafana.yml up --build`
  - open url: <http://localhost:3000/login>
    - login: admin : admin
  - Grafana offers the MongoDB Plugin only for [enterprise version](https://grafana.com/docs/grafana/latest/introduction/grafana-enterprise/) 😡

- using middleware that convert a json request into the mongodb query
  - install as data source: JSON API
  - URL in : <http://middleware:5000>
  - deaad end;

- I  `14-day unlimited usage trial`
  - my dashboard will stop working on 18.09.2024

## Evaluation

### Retrieval Quality

TODO

### Bot Quality

TODO

## General Improvements

TODO
