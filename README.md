# Q&A bot about fact-based diet recommendations

This is a bot intended to help answer questions around a healthy eating and lifestyle habits.

It based on [Dr. Greger's Blog Posts on nutritionfacts.org](https://nutritionfacts.org/blog/) (spanning over ~13 years), which are usually well researched and facts-based.

TODO: expand it

## How I build this bot

### Data Acquisition

- scraped all blog posts from [https://nutritionfacts.org/blog/](https://nutritionfacts.org/blog/) as of 27.08.2024 got from page 1 to 54.
- First blog entries: <https://nutritionfacts.org/blog/page/54/>
- First blog post: April 15, 2011  <https://nutritionfacts.org/blog/welcome-to-nutritionfacts-org/>

## How to run the bot on your own

- clone this repository: `git clone https://github.com/alexkolo/rag_nutrition_facts_blog`

## Python version

- it was build with version `3.12.3`
- setup suggestions using `pyenv`:
  - [install `pyenv` on Linux or MacOS](https://github.com/pyenv/pyenv)
  - [install `pyenv` on Windows](https://github.com/pyenv-win/pyenv-win)

    ```bash
    pyenv install 3.12.x
    pyenv global 3.12.x
    ```

### User Environment

    ```bash
    # assumes Python version 3.12.x
    python -m venv venv  # removed via: sudo rm -rf venv
    source venv/bin/activate # for Linux or MacOS
    # .\venv\Scripts\Activate # for Windows
    pip install -U pip wheel setuptools
    pip install -r requirements.txt
    ```

## Developer Environment

- builds on "Run Environment"
- pre-commit:

    ```bash
    pip install pre-commit
    pre-commit install
    # pre-commit autoupdate
    ```
