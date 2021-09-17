import json
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from models import Base

db = SQLAlchemy(metadata=Base.metadata)


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_file('config.json', load=json.load)
    else:
        app.config.from_mapping(test_config)

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
