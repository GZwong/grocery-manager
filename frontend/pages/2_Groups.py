from typing import List, Dict

import pandas as pd
import streamlit as st
from datetime import datetime as dt
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from frontend import utils

from frontend.layouts.LoginUtils import CredentialsManager

# Start up by inspecting credentials
creds_manager = CredentialsManager()
authenticated = creds_manager.check_authentication()

st.set_page_config(
    page_title="Receipt Viewer",
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
    
    # PAGE STARTS HERE --------------------------------------------------------
    
    # Load username as session_state using user_id
    user_id = st.session_state['user_id']
    username = utils.get_username(user_id)
    st.session_state['username'] = username
    
    # Form - Allow user to create a group
    st.header("Create a group")
    with st.form("Create a group"):

        # Fields
        group_name = st.text_input("Name")
        description = st.text_input("Description")

        submitted = st.form_submit_button("Create")
        
        if submitted:
            status = utils.create_group(group_name, description)
            
            if status:
                st.success("Group successfully created!")
                
                # The user joins the group upon creation
                if utils.add_user_to_group(user_id, group_name):
                    st.success("You have been automatically added to the group!")

            else:
                st.error("Group was not created, try again.")
                    
    st.divider()

    # Get all groups that the user is in
    group_list = utils.get_groups_joined_by_user(user_id)
    
    # User may not be associated with a group
    if not group_list:
        st.header("Join a group to view receipts!")
        st.stop()

    group_name_list = [group["group_name"] for group in group_list]

    # Display groups as a table
    group_df = pd.DataFrame(group_list)
    group_df = group_df.\
        drop(columns=['group_id']).reset_index(drop=True)\
        .rename(columns={
            'group_name': 'Group Name', 
            'description': 'Description'
            })
    
    st.header("Joined groups")
    st.table(group_df)

