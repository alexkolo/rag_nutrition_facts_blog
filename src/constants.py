from pathlib import Path

# paths
# --------
repo_path = Path(".").resolve()  # assumes module is in `./src/`

# data
data_path = repo_path / "data"
blog_posts_root: Path = data_path / "blog_posts"
post_path_json: Path = blog_posts_root / "json"

# database
db_path: Path = repo_path / "databases"
LANCEDB_URI: Path = db_path / "my_lancedb"
