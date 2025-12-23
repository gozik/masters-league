import os

def _env_bool(name, default=False):
    val = os.getenv(name)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "on")


class Config:
    # security: read secret from env (provide a fallback for dev only)
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_key")

    # SQLALCHEMY_DATABASE_URI: use DATABASE_URL environment variable in production
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///database.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # enable/disable debug via env
    DEBUG = _env_bool("DEBUG", False)

    # control file-based behavior (optional)
    APPLICATION_CSV = os.getenv("APPLICATION_CSV", "data/application_list_season254.csv")
    ACTUAL_RESULTS_JSON = os.getenv("ACTUAL_RESULTS_JSON", "data/actual_results.json")

    ACTIVE_SEASON_YEAR = 2026
    ACTIVE_SEASON_NAME = None