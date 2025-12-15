from flask import Flask
from config import Config
from extensions import db, bootstrap


def create_app(config=None):
    app = Flask(__name__)

    if not config:
        config = Config
    app.config.from_object(config)

    # Initialize extensions
    db.init_app(app)
    bootstrap.init_app(app)

    return app