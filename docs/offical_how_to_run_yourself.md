# How you can run & test the chatbot yourself

## Test the deployed Streamlit app

- got to the streamlit app [here](https://dr-greger-blog-bot.streamlit.app/).
- the corresponding dashboard for monitoring the app usage is [here](https://dr-greger-blog-bot-dashboard-usage.streamlit.app/).

> [!NOTE]
> I used Grafana at first for the online dashboard (see [here](https://chatbotdrgreger.grafana.net/public-dashboards/1ae4a1c3c47c41478e16d97aaa5a2276)). However, due to limitation of the free tier version, it stops working properly (aka won't show any data) on 18.09.2024. For the same reason, it will not work locally.
> For more details on my drama around the dashboard see [here](offical_how_i_build_it.md#dashboard).

### Deployment to the streamlit cloud

- create/update the `requirements.txt` file:

  `pip freeze --exclude-editable | sed s/+cpu// > requirements.txt`

- the rest happens within the streamlit cloud account:
  - chatbot app path: `./app.py`
  - dashboard app path: `./dashboard/app.py`
  - `.streamlit/secrets.toml` (same for both apps for simplicity):

      ```plaintext
      GROQ_TOKEN = "gsk_..."

      deployed = true

      [mongodb]
      db_name = "rag_user_info"
      coll_name = "chatbot_dr_greger"
      uri = "mongodb+srv://..."
      ```

## Run it on your own

- add a [Groq API key](https://console.groq.com/keys) in `.streamlit/secrets.toml` as `GROQ_TOKEN = "..."` (since the app is using [Groq Cloud](https://groq.com/) as my LLM API provider, as it is free tier).

### In a container (using docker)

- ensure docker exists: `docker version`
- ensure docker compose exists: `docker compose version`, if not then [install it](https://docs.docker.com/compose/install/linux/)

- using Docker Compose:
  - build & run containers: `docker-compose --env-file=docker.env up --build`
  - view Chatbot in browser: <http://localhost:8501>
  - view Dashboard in browser: <http://localhost:8080>

- for developers (using the dockerfiles):
  - user database (mongodb):
    - start server with `docker-compose --env-file=docker.env --file docker-mongodb.yml up -d`
  - Chatbot (Streamlit App):
    - build container: `docker build -t app:latest .`
    - run container: `docker run -p 8501:8501 app:latest`
    - view in browser: <http://localhost:8501>
  - Dashboard for monitoring (Streamlit App)
    - build container: `docker build -f dashboard/Dockerfile -t dashboard .`
    - run container: `docker run -p 8080:8080 dashboard`
    - view in browser: <http://localhost:8080>

### From the source code

- clone this repository: `git clone https://github.com/alexkolo/rag_nutrition_facts_blog`

- get the right Python version
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

- user database (mongodb):
  - start the server with `docker-compose --env-file=docker.env --file docker-mongodb.yml up -d`
- Chatbot (Streamlit App):
  - start it via `streamlit run ./app.py --server.port 8501`
  - view in browser: <http://localhost:8501>
- Dashboard for monitoring (Streamlit App):
  - start it via `streamlit run ./dashboard/app.py --server.port 8080`
  - view in browser: <http://localhost:8080>
