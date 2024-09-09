# How you can run & test the chatbot yourself

## In the cloud (aka deployed)

- got to the streamlit app [here](https://dr-greger-blog-bot.streamlit.app/).
- the corresponding dashboard for monitoring the app usage is [here](https://chatbotdrgreger.grafana.net/public-dashboards/1ae4a1c3c47c41478e16d97aaa5a2276).

    > [!IMPORTANT]
    > The online dashboard will stop working properly (aka won't show any data) on 18.09.2024 due to the 14-day trial period ending by Grafana. 😭
  - I'm using a MongoDB plugin that is only available for the Enterprise version of Grafana. Unfortunately, I found this out only after setting up my own MongoDB and creating the dashboard. 😒
  - I tried to rebuild it using MongoDB's own dashboard tool "Charts". See the result [here](https://charts.mongodb.com/charts-project-0-dwgewmy/public/dashboards/10ed0c93-9fb1-4b89-a1e3-966fddef4f27). However, I was only able to reproduce the simplest panels. Moreover, I couldn't figure out to set up a time filter as in Grafana. 😓

## Run it on your own

- add a [Groq API key](https://console.groq.com/keys) in `.streamlit/secrets.toml` as `GROQ_TOKEN = "..."` (since the app is using [Groq Cloud](https://groq.com/) as my LLM API provider, as it is free tier).

> [!NOTE]
> There is no local dashboard to monitor the app usage, since Grafana doesn't offer the MongoDB data plugin for the free tier. [Source](https://grafana.com/docs/grafana/latest/introduction/grafana-enterprise/#enterprise-data-sources) (see comment above for the deployed version)

### In a container (using docker)

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

### From the source code

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
