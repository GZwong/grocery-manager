# Standard Imports
import requests
import logging
from functools import wraps
from typing import List, Dict

# Third-Party Imports
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile  # For docs

# Base URL for API
BASE_URL = "http://127.0.0.1:5000"

# logging
logger = logging.getLogger("Testing backend API")
logging.basicConfig(filename='myapp.log', level=logging.INFO)


def get_username(user_id: int):
    response = requests.get(f"{BASE_URL}/user/get/username/{user_id}")
    if response.status_code == 200:
        return response.json()['username']    
    return None

def get_user_id(username: str):
    response = requests.get(f"{BASE_URL}/user/get/user-id/{username}")
    if response.status_code == 200:
        return response.json().get('user_id')
    return None

def get_user_email(user_id: int):
    
    response = requests.get(f"{BASE_URL}/user/get/email/{user_id}")
    
    if response.status_code == 200:
        return response.json()['email']
    return None

def get_all_groups() -> List[Dict]:
    
    response = requests.get(f"{BASE_URL}/groups/get-all")
    
    if response.status_code == 200:
        return response.json()
    return None

def get_groups_joined_by_user(user_id: int):
    """
    Inputs
    ------
    user_id: int
        User ID of current session
    
    Returns
    -------
    list[Dict] | None
        A list of dictionaries with each element corresponding information
        of a group. This is None if the user is not associated with any group
        E.g.
            [
                {
                    "group_id": 1,
                    "group_name": "Example Group Name",
                    "description": "Example Group Description"
                },
                {
                    "group_id": 2,
                    "group_name": "Another Example Group Name",
                    "description": "Another Example Group Description"
                }
            ]
    """
    
    response = requests.get(f"{BASE_URL}/user/get/groups/{user_id}")
    
    if response.status_code == 200:
        return response.json()
    return None


def create_group(name: str, description: str) -> bool:
    """
    Return True if group is created, False if request failed.
    """
    data = {"name": name, "description": description}
    response = requests.post(f"{BASE_URL}/groups/create", json=data)
    
    if response.status_code == 200:
        return True
    return False

def delete_group(name: str) -> bool:
    """
    Return True if group is deleted, False if request failed.
    """
    data = {"group_name": name}
    response = requests.delete(f"{BASE_URL}/groups/delete", json=data)
    
    if response.status_code == 200:
        return True
    return False


def add_user_to_group(user_id: int, group_name: str) -> dict:
    
    data = {"user_id": user_id, "group_name": group_name}
    response = requests.post(f"{BASE_URL}/groups/add-user-to-group", json=data)
    
    if response.status_code == 200:
        return True
    return False


def add_receipt_to_group(pdf_file: UploadedFile, group_id: int) -> bool:
    
    file = {"file": (pdf_file.name, pdf_file.getvalue(), pdf_file.type)}
    data = {"group_id": group_id}

    response = requests.post(f"{BASE_URL}/receipt/add", files=file, data=data)
    if response.status_code == 200:
        return True
    return False

def get_receipt_list_in_group(group_id: int):
    """
    Return a list of receipts in the form of dictionaries each with the
    following fields:
        - "receipt_id"
        - "slot_time"
        - "total_price"
        - "payment_card"
    """

    response = requests.get(f"{BASE_URL}/receipt/get-receipt-list/{group_id}")
    
    if response.status_code == 200:
        receipt_list: List[Dict] = [receipt_info for receipt_info in response.json()["receipts"]]
        return receipt_list
    return False

def get_receipt_data(receipt_id: int):
    
    response = requests.get(f"{BASE_URL}/receipt/get/{receipt_id}")
    
    if response.status_code == 200:
        item_list: List[Dict] = [item_info for item_info in response.json()["items"]]
        return item_list
    return False


def get_users_in_receipt(receipt_id: int):
    response = requests.get(f"{BASE_URL}/receipt/get/user-items/{receipt_id}")
    if response.status_code == 200:
        if response:
            user_item_association = response.json()
            if "user_item_association" in user_item_association:
                return user_item_association["user_item_association"]
    else:
        return False
    
def update_user_item_association(data):
    response = requests.put(f"{BASE_URL}/receipt/update/user-items", json=data)
    if response.status_code == 200:
        return True
    return False

def add_user_to_receipt(user_id: int, receipt_id: int):
    data = {'user_id': user_id, 'receipt_id': receipt_id}
    response = requests.post(f"{BASE_URL}/receipt/update/user-items", json=data)
    if response.status_code == 200:
        return True
    return False


def get_users_in_group(group_id: int) -> List[Dict]:
    """
    Return
        [
            {"user_id": 1, "username": user1},
            {"user_id": 2, "username": user2}
        ]
    Otherwise return False
    """
    response = requests.get(f"{BASE_URL}/groups/in/{group_id}")
    if response.status_code == 200:
        return response.json()
    return False
