"""
run.py

This script is to be used when running locally. It is the same copy as `app.py`
which is intended as the backend entrypoint.
"""
# Standard Imports
import os
import sys

# Add the parent folder to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
