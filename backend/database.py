"""
Defines database connection configuration and a session object used for
database transaction. Also creates the defined tables in `models.py` upon
connection.

Dependencies: models.py
"""
# Standard Imports
import argparse
import os
from contextlib import contextmanager
from pathlib import Path

# Third-Party Imports
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Project-Specific Imports
from backend.models import Base


# Determine if flask app utilizes local SQLite database or remote PostgreSQL
parser = argparse.ArgumentParser()
parser.add_argument('--local', action='store_true', help="Run the app locally with SQLite")
args = parser.parse_args()
if args.local:
    # Local SQLite database
    db_path = Path(__file__).resolve().parent.parent / "groceries.db"
    DATABASE_URL = f"sqlite:///{db_path}"
    print("Running with local SQLite database...")
else:
    # Load environment variables for remote database
    load_dotenv()
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")
    print("Running with remote database...")


# Specify the schema
metadata = MetaData(schema='finance')  # TODO: This does not seem to work
Base.metadata = metadata

# Create Engine
engine = create_engine(DATABASE_URL)

# Session object for database transaction sessions
@contextmanager
def SessionLocal():
    """
    Context manager to make transactions around database.
    
    Example Usage:
        with SessionLocal() as session:
            user = session.query(User).filter_by(User.user_id=user_id).first()
    """
    session_blueprint = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_blueprint()
    
    try:
        yield session
        session.commit()
        
    except Exception as e:
        session.rollback()
        raise e 
    
    finally:
        session.close()

# Create tables (IF NOT EXISTS)
Base.metadata.create_all(bind=engine)
