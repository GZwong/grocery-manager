"""
The home page showing user statistics.
"""
# Standard Imports
import os
import sys
from datetime import datetime as dt

# Third-Party Imports
import streamlit as st

# Project-Specific Imports
# Add the parent folder to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import frontend.api_client as api
from layouts.LoginUtils import CredentialsManager
from components.UserSpendingViewer import UserSpendingViewer

# Start up by inspecting credentials
creds_manager = CredentialsManager()
authenticated = creds_manager.check_authentication()

st.set_page_config(
    page_title="Home",
    layout="wide"
)

# Login / Registration / Password Reset Form
if not authenticated:
    
    creds_manager.login_form()
    creds_manager.register_form()

    # Rerun the application if user becomes authenticated
    authenticated = creds_manager.check_authentication()
    if authenticated: st.rerun()

else:
    
    # PAGE STARTS HERE --------------------------------------------------------
    
    # Load username as session_state using user_id
    user_id = st.session_state['user_id']
    username = api.get_username(user_id)
    email = api.get_user_email(user_id)
    st.session_state['username'] = username
    
    # Display user information
    st.title(username)
    st.markdown(f"**User ID**: {user_id}")
    st.markdown(f"**Email**: {email}")
    
    # Display line chart showing the cost spent per receipt
    spending_viewer = UserSpendingViewer(user_id)
