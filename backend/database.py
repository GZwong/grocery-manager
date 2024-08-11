"""
This file creates the data tables defined in 'models.py' within the database,
and return a Session object to be used for database transactions.

Dependencies: models.py
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Project-Specific Imports
from models import Base
from path_management.base import get_database_path


DATABASE_URL = f"sqlite:///{get_database_path()}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)
