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
DATA_PATH: Path = REPO_PATH / "data"
blog_posts_root: Path = DATA_PATH / "blog_posts"
POST_JSON_PATH: Path = blog_posts_root / "json"
IMAGE_PATH: Path = DATA_PATH / "images"

# Chat bot


# database
db_path: Path = REPO_PATH / "databases"
LANCEDB_URI: Path = db_path / "my_lancedb"


# RAG config file
RAG_CONFIG_TOML: Path = REPO_PATH / "rag_config.toml"


def get_rag_config() -> dict:
    with open(RAG_CONFIG_TOML, mode="rb") as toml_file:
        config = tomli.load(toml_file)
    return config


# Chat bot
# ==========================

# keys in `st.session_state`
# ----------------
MESSAGES: str = "messages"

# Assets
# ----------------
BOT_AVATAR: Path = IMAGE_PATH / "dr-greger_f1b10472.png"
APP_ASSETS: Path = DATA_PATH / "app_assets"
BOT_DISCLAIMER: Path = APP_ASSETS / "chat_bot_disclaimer.md"


# User info
# -----------------------------
USER_DB_NAME = "bot_usage"
USER_COLL_NAME = "user_info"
USER_INFO_TEMPLATE = {
    "user_id": None,
    "timestamp": None,
    "user_language": None,
    "like_bot": None,
    "n_sessions": None,
    "chat_history": None,
}
