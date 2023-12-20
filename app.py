# Third-Party Imports
import streamlit as st
import pandas as pd

# Project-Specific Imports
from src.ReceiptClasses.SainsburysReceipt import SainsburysReceipt
from database_management.OrderDataManager import OrderDataManager
from database_management.UserDataManager import UserDataManager


# Set page layout to be wide
st.set_page_config(layout="wide")
st.title("Grocery Receipt Reader (Sainsbury's)")

# Set up OrderDataManager object to manipulate order datatable in the database
OrderData = OrderDataManager()

# Upload and read receipt
col1, col2, col3 = st.columns([5, 3, 1])

with col1:
    receipt = st.file_uploader("Upload receipt", type=["pdf"])
    read_status = st.empty()
    
    if receipt:
        read_status.text("Reading pdf file...")
        receipt = SainsburysReceipt(receipt)
        OrderData.upload_order(receipt)
        read_status.text("Done reading pdf file")

with col2:
    # Process data, then display it
    order_dates = OrderData.get_all_dates()
    selected_date = st.selectbox('Choose from uploaded receipts:', order_dates)
    # (Backend) Initialize the user data for the selected_date
    UserData = UserDataManager(selected_date)
    
with col3:
    # Enable option to delete receipt if an order date is selected
    if selected_date:
        if st.button("Delete this receipt"):
            OrderData.delete_order_by_date(selected_date)
            st.experimental_rerun()


# Initialize the user data for the selected_date
UserData = UserDataManager(selected_date)


# These display only when a date is selected
if selected_date:
        
    col1, col2, col3, col4 = st.columns([3, 1, 1, 4])

    with col1:
        username = st.text_input(label="Add new user here", 
                                 label_visibility='collapsed',
                                 placeholder='Enter a username to be added/deleted')    

    with col2:
        if st.button("Add User"):
            UserData.add_user(username)
            st.experimental_rerun()

    with col3:
        if st.button("Delete User"):
            UserData.delete_user(username)
            st.experimental_rerun()
    
    # Show the dataframe
    user_df = st.data_editor(UserData.show_user_df())
    
    # CALCULATE PRICE
    # ---------------
    # Assume all columns after 'price' is the username
    # price_col_number = user_df.columns.get_loc('price')
    username_list = UserData.get_usernames()
    
    # Perform a deep copy of the dataframe so that the original remains unmodified
    summary_df = user_df.copy(deep=True)   
    summary_df['Number of Buyer'] = summary_df[username_list].sum(axis=1)  # Total number of buyers that bought each item
    summary_df['Price Per User'] = summary_df.apply(lambda row: row['price'] / row['Number of Buyer'] if row['Number of Buyer'] > 0 else 0, axis=1)

    # Calculate price per user for all users
    for username in username_list:
        summary_df[username] = summary_df[username] * summary_df['Price Per User']
    # This results in a PANDAS SERIES where each row coresponds to a user
    summary_df = summary_df[username_list].sum()
    summary_df.name = 'Individual Payable Amount (£)'
    
    # Show this dataframe
    st.dataframe(summary_df)

    # User options
    if st.button("Save to Database"):
        UserData.save_user_df(user_df)
