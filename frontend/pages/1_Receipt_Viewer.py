from typing import List, Dict, Set

import pandas as pd
import streamlit as st
from datetime import datetime as dt

# Project-Specific Imports
from frontend import utils
from frontend.ReceiptEditor import ReceiptEditor
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

    # Get all groups that the user is in
    group_list: List[Dict] = utils.get_groups_joined_by_user(user_id)
    
    # User may not be associated with a group
    if not group_list:
        st.header("Join a group to view receipts!")
        st.stop()

    # Store a list of group names and display in select box
    group_name_list = [group["group_name"] for group in group_list]

    selected_group_name = st.selectbox(
        label="Which group of receipts do you want to see?",
        options=group_name_list
    )
    
    # Only display a receipt if a group is selected
    if selected_group_name:
        
        # Find group_id of selected group
        for group in group_list:
            if group["group_name"] == selected_group_name:
                selected_group_id = group["group_id"]
    
        # Upload Receipt
        uploaded_receipt = st.file_uploader("Upload a receipt to the group", type=["pdf"], accept_multiple_files=False)
        if uploaded_receipt:
            receipt_upload_status = utils.add_receipt_to_group(uploaded_receipt, selected_group_id)
            if receipt_upload_status:
                st.success("Receipt has been uploaded successfully")
            # TODO: Check if this receipt has been uploaded before

        # Get list of receipts to display
        receipt_list: List[Dict] = utils.get_receipt_list_in_group(selected_group_id)
        if receipt_list:
            receipt_time_list = [receipt["slot_time"] for receipt in receipt_list]
            selected_receipt = st.selectbox(
                label="Select receipt to view",
                options=receipt_time_list
            )
        else:
            st.error("Receipts not found")
            st.stop()
        
        # Display receipt if selected
        if selected_receipt:
            
            # Get the selected receipt ID
            for receipt in receipt_list:
                if receipt["slot_time"] == selected_receipt:
                    selected_receipt_id = receipt["receipt_id"]
            
            # Query with receipt ID to fetch receipt
            receipt_data: List[Dict] = utils.get_receipt_data(selected_receipt_id)
            if receipt_data:
                # Check if there are users associated with this receipt already
                # If True, combine it with current data
                user_items_selection: List[Dict] = utils.get_users_in_receipt(selected_receipt_id)
                if user_items_selection:
                    
                    # Find the mapping between the obtained user_ids and usernames
                    user_ids_in_receipt  = {user['user_id'] for user in user_items_selection}
                    usernames_in_receipt = {utils.get_username(id) for id in user_ids_in_receipt}
                    user_mapping = dict((id, name) for id, name in zip(user_ids_in_receipt, usernames_in_receipt))
                    
                    # Merge the two tables via ReceiptEditor class
                    items_df = pd.DataFrame(receipt_data)
                    user_items_df = pd.DataFrame(user_items_selection)  # Take out weight for now... process this later
                    receipt_grid = ReceiptEditor(items_df, user_items_df, user_mapping)
                    
                else:
                    items_df = pd.DataFrame(receipt_data)
                    receipt_grid = ReceiptEditor(items_df)
                
                # Allow users not in the receipt to be added
                # Get all users in the group
                user_list : List[Dict] = utils.get_users_in_group(selected_group_id)
                # Find out which user has not been added to the receipt and get their names (Use a set to use intersection)
                user_ids_in_receipt      = {user['user_id'] for user in user_items_selection}
                user_ids_in_group        = {user['user_id'] for user in user_list}
                usernames_not_in_receipt = [utils.get_username(id)
                                            for id in user_ids_in_group 
                                            if id not in user_ids_in_receipt]
                # Get a selectbox to (potentially) add new users to the receipt
                selected_username = st.selectbox(
                    label='Add a member to this receipt?',
                    index=None,  # No value initially
                    options=usernames_not_in_receipt,
                )
                if st.button("Add") and selected_username:
                    add_user_id = utils.get_user_id(selected_username)
                    if utils.add_user_to_receipt(add_user_id, selected_receipt_id):
                        st.rerun()
