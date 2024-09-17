from typing import List, Dict

import pandas as pd
import streamlit as st
from datetime import datetime as dt
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

    # Get all groups joined by user
    group_list = utils.get_groups_joined_by_user(user_id)
    
    # Join Groups    
    group_name_to_join = st.text_input(
        "Join a group 👇",
        placeholder="Group Name",
    )
    if group_name_to_join:
        if utils.add_user_to_group(user_id, group_name_to_join):
            st.success("You have been added to the group!")
            st.rerun()
          
    # Stop rendering the rest if user has not joined any groups  
    if not group_list:
        st.stop()
    
    st.divider()
    
    # Show all joined groups
    st.header("Joined Groups")
    
    # Create an expander for each group
    for idx, group in enumerate(group_list):
        
        with st.expander(f"{group['group_name']}"):
            
            st.caption(group["description"])
            
            col1, col2, col3 = st.columns([5, 3, 2])
            
            # Look at receipt button
            with col1:
                pass
            
            # Add Other User(s) Button
            with col2:
                username_to_add = st.text_input(label="Add a user 👇",
                                                placeholder="Username",
                                                # Pass unique key
                                                key=f'add-user-{idx}')
                if username_to_add:
                    user_id_to_add = utils.get_user_id(username_to_add)
                    if utils.add_user_to_group(user_id_to_add, group['group_name']):
                        st.success("User added to group")
                        st.rerun()
            
            # Delete Group Button - Add popover for confirmation
            with col3:
                with st.popover("Delete group"):
                    st.caption("Are you sure you want to delete this group?")
                    delete_button = st.button(label="Yes",
                                            key=f'delete-group-{idx}')
                    if delete_button:
                        utils.delete_group(group['group_name'])
                        st.rerun()
                    
    st.divider()
    
    # Form - Allow user to create a group
    with st.form("Create a group", border=False):
        
        st.write("Create a group")

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
                    st.rerun()

            else:
                st.error("Group was not created, try again.")
