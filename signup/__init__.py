import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from config import config
from models import Base

db = SQLAlchemy(metadata=Base.metadata)


def create_app(additional_config=None):
    app = Flask(__name__)

    app.config.update(config)
    if additional_config:
        app.config.update(additional_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    with app.app_context():
        db.create_all()

        from .routes import bp
        app.register_blueprint(bp)

        return app


if __name__ == '__main__':
    create_app().run()
