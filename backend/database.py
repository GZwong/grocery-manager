"""
Defines database connection configuration and a session object used for
database transaction. Also creates the defined tables in `models.py` upon
connection.

Dependencies: models.py
"""
# Standard Imports
from contextlib import contextmanager

# Third-Party Imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Project-Specific Imports
from models import Base
from path_management.base import get_database_path


DATABASE_URL = "postgresql://postgres:Game6Klay!2002@localhost/grocery_manager"
DATABASE_URL = f"sqlite:///{get_database_path()}"

engine = create_engine(DATABASE_URL)

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


# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)
