"""
ResponseWrapper.py

Defines a class of ResponseWrapper that wraps around the response from the
standard request library with useful methods and attributes.
"""
from requests import Response


class ResponseWrapper:
    """
    Creates an instance of a ResponseWrapper class.
    """
    
    def __init__(self, response: Response):
        
        self.status_code = response.status_code
        self.success == (response.status_code == 200)
        self.message = self.extract_message(response)
        self.data = self.extract_data(response)
        
    def extract_message(self, response: Response):
        try:
            return response.json().get("message", "No message provided")
        except ValueError:
            return "No JSON response received"
    
    def extract_data(self, response: Response):
        try:
            return response.json().get("data", None)
        except ValueError:
            return None
