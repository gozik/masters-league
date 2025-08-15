from flask import Flask
from config import Config
from extensions import db, bootstrap


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    bootstrap.init_app(app)

    return app