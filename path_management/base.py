from pathlib import Path


def get_base_path():
    """
    Get the root directory of the project.
    """
    
    return Path(__file__).resolve().parent.parent


def get_database_path():
    """
    Get the path to "groceries.db"
    """
    return get_base_path() / "groceries.db"
