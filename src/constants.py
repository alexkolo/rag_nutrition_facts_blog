from pathlib import Path

import tomli

# paths
# --------


# get root of repository
def find_repo(path):
    """Find repository root from the path's parents"""
    for path in Path(path).parents:  # here "path" is redefined as parent
        if (path / "src").is_dir():
            return path


REPO_PATH = find_repo(__file__)  # Path(".").resolve()  # assumes module is in `./src/`

# data
data_path = REPO_PATH / "data"
blog_posts_root: Path = data_path / "blog_posts"
POST_JSON_PATH: Path = blog_posts_root / "json"

# database
db_path: Path = REPO_PATH / "databases"
LANCEDB_URI: Path = db_path / "my_lancedb"


# RAG config file
RAG_CONFIG_TOML: Path = REPO_PATH / "rag_config.toml"


def get_rag_config() -> dict:
    with open(RAG_CONFIG_TOML, mode="rb") as toml_file:
        config = tomli.load(toml_file)
    return config