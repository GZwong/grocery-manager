"""
app.py

Main backend entrypoint
"""
# Standard Imports
import os
import sys

# Add the parent folder to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend import create_app
from backend.models import Base

app = create_app()
