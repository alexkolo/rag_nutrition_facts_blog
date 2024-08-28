# Q&A bot about fact-based diet recommendations

This is a bot intended to help answer questions around a healthy eating and lifestyle habits.

It based on [Dr. Greger's Blog Posts on nutritionfacts.org](https://nutritionfacts.org/blog/) (spanning over ~13 years), which are usually well researched and facts-based.

TODO: expand it

## How I build this bot

### Data Acquisition

- I scraped all blog posts from [https://nutritionfacts.org/blog/](https://nutritionfacts.org/blog/) as of 28.08.2024
- Notebook: `notebooks/web_scraping.ipynb`
  - At first, at collected the urls of all blog posts: `data/blog_posts/blog_posts_urls.csv`
    - Number of unique blog post urls: 1281
  - Then I saved the content of each blog post a json file in `data/blog_posts/json/` with the following structure:
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

### Data Ingestion

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

- create "User Environment"
- `pip install -r requirements_dev.txt`
- (optional) pre-commit setup: `pre-commit install` (update: `pre-commit autoupdate`)
