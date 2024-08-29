# Q&A bot about fact-based diet recommendations

This is a bot intended to help answer questions around a healthy eating and lifestyle habits.

It based on [Dr. Greger's Blog Posts on nutritionfacts.org](https://nutritionfacts.org/blog/) (spanning over ~13 years), which are usually well researched and facts-based.

## Docs

- [How I build this bot](docs/how_to_build.md)

## Problem statement

TODO: expand it

## How to run the bot on your own

- clone this repository: `git clone https://github.com/alexkolo/rag_nutrition_facts_blog`

## Python version

- it was build with version `3.12.3`
- setup suggestions using `pyenv`:

  ```bash
  pyenv install 3.12.x
  pyenv global 3.12.x
  ```

  - [install `pyenv` on Linux or MacOS](https://github.com/pyenv/pyenv)
  - [install `pyenv` on Windows](https://github.com/pyenv-win/pyenv-win)

### User Environment

    ```bash
    # assumes Python version 3.12.x
    python -m venv venv  # removed via: sudo rm -rf venv
    source venv/bin/activate # for Linux or MacOS
    # .\venv\Scripts\Activate # for Windows
    pip install -U pip wheel setuptools
    pip install -r requirements.txt
    pip cache purge # reduce storage footprint
    ```

## Developer Environment

- create "User Environment"
- `pip install -r requirements-dev.txt`
- (optional) pre-commit setup: `pre-commit install` (update: `pre-commit autoupdate`)
  - test: `pre-commit run --all-files`
