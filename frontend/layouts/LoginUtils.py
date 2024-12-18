# Standard Imports
import os
import requests

# Third-Party Imports
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv('BACKEND_URL')

class CredentialsManager(object):
    
    def __init__(self):
        pass
            
    def _register_user(self, username: str, password: str, email: str):
        data = {'username': username, 'password': password, 'email': email}
        response = requests.post(f"{BASE_URL}/users", json=data)
        print(response.json())
        if response.status_code == 201:
            return True
        return False

    def _login(self, username, password):
        data = {"username": username, "password": password}
        response = requests.post(f"{BASE_URL}/users/login", json=data)
        
        # If backend authenticated, save token as streamlit session_state
        # for global 
        if response.status_code == 200:
            
            # Extract JWT
            data = response.json()  # Extract JWT
            token = data.get("access_token", None)
            user_id = data.get("user_id", None)
            
            st.session_state["authenticated"] = True
            st.session_state['access_token'] = token
            st.session_state['user_id'] = user_id
        
        return response
    
    def _set_new_password(username):
        """
        Set a new password for the given user, and email the new password to
        the user's email.
        """
        return None
    
    def check_authentication(self):
        """
        Check authentication status through streamlit session state.
        """
        authenticated = st.session_state.get('authenticated', False)
        return authenticated

    def login_form(self):
        """
        Renders a login form.
        """
        with st.form("login"):
            
            # Title
            st.write("Login")

            # Fields
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            submitted = st.form_submit_button("Log in")
            
            if submitted:
                login_state = self._login(username, password)
                
                if login_state.status_code == 200:
                    st.success("Login Successful!")
                else:
                    st.error("Invalid username or password.")
                    
    def register_form(self):
        """
        Renders a registration form.
        """    
        with st.form("Register as new user", clear_on_submit=True):
            
            # Title
            st.write("Register as a new user")
            
            # Fields
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            email = st.text_input("Email")
            
            register_button = st.form_submit_button("Register")
                    
            if register_button:
                register_success = self._register_user(username, password, email)
                
                if register_success:
                    st.success("Registration successful!")
                    self._login(username, password)
                else:
                    st.error(f"Registration error. Please try again.")
