import requests
import streamlit as st
from datetime import datetime as dt
from frontend import utils

from frontend.layouts.LoginUtils import CredentialsManager

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
    
    # For debugging purposes
    st.write("Current session state:")
    for key, value in st.session_state.items():
        st.write(f"----- {key}: {value}")

    # Rerun the application if user becomes authenticated
    authenticated = creds_manager.check_authentication()
    if authenticated: st.rerun()

else:
    
    with st.sidebar:
        st.button("Logout")
    
    # PAGE STARTS HERE --------------------------------------------------------
    
    # Load username as session_state using user_id
    user_id = st.session_state['user_id']
    username = utils.get_username(user_id)
    st.session_state['username'] = username
    
    st.title(f"Welcome, {username}!")
