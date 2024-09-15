import os
from flask import Flask

# Routes
from routes.groups.routes import groups_blueprint
from routes.users.routes import user_blueprint
from routes.receipts.routes import receipt_blueprint

# MAIN CODE HERE
app = Flask(__name__)
app.register_blueprint(groups_blueprint, url_prefix='/groups')
app.register_blueprint(user_blueprint, url_prefix='/user')
app.register_blueprint(receipt_blueprint, url_prefix='/receipt')

app.secret_key = os.urandom(24)  # Generate a 24-byte random key

if __name__ == '__main__':
    app.run(debug=True)
