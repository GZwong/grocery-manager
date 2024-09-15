# logging.py
import os
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Configure handlers
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('flask.log')

# Set logging format

# Define a custom formatter that logs the parent folder and filename
class CustomFormatter(logging.Formatter):
    def format(self, record):
        # Get the full pathname of the module where the log message was generated
        full_path = record.pathname
        
        # Extract the filename
        filename = os.path.basename(full_path)
        
        # Extract the parent folder name
        parent_folder = os.path.basename(os.path.dirname(full_path))
        
        # Modify the log message format
        record.custom_filepath = f"{parent_folder}/{filename}"
        
        # Now use this in the log message format
        return super().format(record)

# Create a log format with the custom filepath
formatter = CustomFormatter('%(asctime)s - %(custom_filepath)s - %(levelname)s - %(message)s')

console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)
