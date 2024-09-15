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
                    items_df = pd.DataFrame(receipt_data)
                    user_items_df = pd.DataFrame(user_items_selection).drop('weight', axis=1)  # Take out weight for now... process this later
                    receipt_grid = ReceiptEditor(items_df, user_items_df, {1: "Gai"})
                    receipt_grid.render_grid()
                    
                    # Render a button to submit changes in the dataframe
                    if st.button("Submit Changes"):
                        # updated_df = receipt_grid.grid_data()
                        
                        # # Prepare a dictionary of an empty list to store dictionaries of user item association 
                        # updated_user_item_association = {"user_items": []}
                        
                        # user_ids_in_receipt = {user['user_id'] for user in user_items_selection}
                        # for id in user_ids_in_receipt:
                        #     filtered_df = updated_df.loc[:, [str(id), "item_id", "quantity", "weight"]]  # This is a dataframe with two columns: user and items
                        #     for index, row in filtered_df.iterrows():
                        #         updated_user_item_association["user_items"].append(
                        #             {"user_id": int(id),
                        #              "item_id": int(row['item_id']),
                        #              "quantity": 0 if pd.isna(row["quantity"]) else row["quantity"],
                        #              "weight": 0 if pd.isna(row["weight"]) else row["weight"]}
                        #         )
                        
                        # st.write(updated_user_item_association)
                        # if utils.update_user_item_association(updated_user_item_association):
                        #     st.success("User Item Association updated successfully!")
                        status = receipt_grid.save_changes()
                        if status:
                            st.success("Updated successfully!")
                    
                else:
                    st.dataframe(receipt_data)
                
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
                        st.success(f"{selected_username} has been successfully added!")
                


    # user_list: List[Dict] = utils.get_user_list().json()

    # receipt = st.file_uploader("Upload receipt", type=["pdf"])
    # if receipt:
    #     receipt = SainsburysReceipt(receipt)
    #     utils.add_receipt(receipt, selected_group)

    # get_receipt_response = utils.get_receipt_list_in_group(selected_group)
    # if get_receipt_response.status_code == 200:
    #     receipt_list = get_receipt_response.json()['receipts']
    #     selected_date = st.selectbox("Choose from uploaded receipts: ", [dt.fromtimestamp(receipt['slot_time']) for receipt in receipt_list])

    #     receipt_info = utils.get_user_item_associations(869874627)
    #     receipt_info_dict = receipt_info.json()["items"]
    #     print(receipt_info_dict)
    #     # st.text(receipt_info.text)

    #     flattened_data = []
    #     for item in receipt_info_dict:
    #         row = {
    #             "Name": item["item_name"],
    #             "Quantity": item["total_quantity"],
    #             "Weight": item["total_weight"],
    #         }
    #         for user in item["users"]:
    #             user_id = user["user_id"]
                
    #             # Find the username of this user_id
    #             for i in user_list:
    #                 if i['user_id'] == user_id:
    #                     username = i['username']
    #                     break
                    
    #             # Add each user as row, noting that one of item weight and quantity
    #             # is not none
    #             row[username] = user["quantity"] if item["total_quantity"] else user["weight"]

    #         flattened_data.append(row)
            
            
    #     df = pd.DataFrame(flattened_data)
        
    #     # Configure the grid
    #     gb = GridOptionsBuilder()
    #     gb.configure_column("Name", editable=False)
    #     gb.configure_column("Quantity", editable=False, type=["numericColumn", "numberColumnFilter", "floatingFilter"])
    #     gb.configure_column("Weight", editable=False, type=["numericColumn", "numberColumnFilter", "floatingFilter"])
        
    #     # Configure the rest of the columns as editable
    #     for col in df.columns:
    #         if col not in ["Name", "Quantity", "Weight"]:
    #             gb.configure_column(col, editable=True)
    #     go = gb.build()

    #     AgGrid(df, gridOptions=go, update_mode=GridUpdateMode.NO_UPDATE)
