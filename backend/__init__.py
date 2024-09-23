import os

# Third-Party Imports
from flask import Flask

# Routes
from backend.routes.group_routes import groups_blueprint
from backend.routes.user_routes import user_blueprint
from backend.routes.receipt_routes import receipt_blueprint

# MAIN CODE HERE
def create_app():
    app = Flask(__name__)
    app.register_blueprint(groups_blueprint,  url_prefix='/groups')
    app.register_blueprint(user_blueprint,    url_prefix='/user')
    app.register_blueprint(receipt_blueprint, url_prefix='/receipt')

    app.secret_key = os.urandom(24)  # Generate a 24-byte random key

    return app
