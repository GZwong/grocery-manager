# Standard Imports
import sqlite3
import pandas as pd
from datetime import datetime
from typing import Union

# Project-specific Imports
from path_management.base import get_database_path
from data_management.OrderDataManager import OrderDataManager


# Absolute Path to the sqlite3 database
DATABASE_FILE = get_database_path()


class UserDataManager():
    """
    Manage the user data for a specific order_date.
    
    When initialized, get a copy of the dataframe for existing user selections for that date. Return an empty dataframe
    if there were no prior selections.
    
    """
    
    def __init__(self, order_date: Union[datetime, str]):
        
        self.order_date = order_date
        # self.database_df = None
        
        # Create the required database tables IF NOT YET EXISTS
        self._create_user_selections_table()
        # Load the current user_selections to dataframe
        self._read_current_user_selections()
        

    def _create_user_selections_table(self):
        """Create the "user_selections" table within the database."""

        with sqlite3.connect(DATABASE_FILE) as conn:
            # Enable foreign key support
            conn.execute("PRAGMA foreign_keys = ON;")
            # Create "user_selections" table as the child table of "order_items".
            # Hence deleting the order date will delete all relevant selections.
            # TODO: CHANGE SELECTION TO BOOLEAN FOR OTHER DATABASES
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_selections(
                    id INTEGER PRIMARY KEY,
                    item_id INTEGER,
                    user_id TEXT,
                    selection INTEGER DEFAULT 0,
                    FOREIGN KEY (item_id) REFERENCES order_items(item_id)
                    ON DELETE CASCADE
                )
                         """)
    
        
    def _read_current_user_selections(self):
        """Read the current user_selections table from the database"""
        
        with sqlite3.connect(DATABASE_FILE) as conn:
            query = """
                SELECT * FROM user_selections AS us
                WHERE us.item_id IN (
                    SELECT items.item_id FROM order_items AS items
                    WHERE items.order_id IN (
                        SELECT info.order_id FROM order_info AS info
                        WHERE info.order_date = ?
                    )
                )
            """
            df = pd.read_sql_query(query, conn, params=[self.order_date, ])
        return df
    
    
    def get_usernames(self):
        """Load a list of the current usernames in the database for that order"""
        with sqlite3.connect(DATABASE_FILE) as conn:
            query = """
                SELECT DISTINCT us.user_id FROM user_selections AS us
                WHERE us.item_id IN (
                    SELECT items.item_id FROM order_items AS items
                    WHERE items.order_id IN (
                        SELECT info.order_id FROM order_info AS info
                        WHERE info.order_date = ?
                    )
                )
                """
            usernames = pd.read_sql_query(query, conn, params=[self.order_date])
        return usernames['user_id'].to_list()


    def add_user(self, username: str):
        """Add a user column to the database and update the class attribute to reflect the change"""
                
        # If this user exists, then terminate the function
        if username in self.get_usernames():
            return None
        
        # Define query to obtain unique item_ids for that specified date
        query = """
            SELECT DISTINCT item_id FROM order_items AS items
            WHERE items.order_id IN (
                SELECT info.order_id FROM order_info AS info
                WHERE info.order_date = ?
            )
        """
        with sqlite3.connect(DATABASE_FILE) as conn:
            
            # Get the list of unique item_ids
            item_id_column = pd.read_sql_query(query, conn, params=[self.order_date])
            
            # For each item_id, create a new row for that user
            for item_id in item_id_column["item_id"]:
                insert_query = "INSERT INTO user_selections (item_id, user_id) VALUES (?, ?);"
                conn.execute(insert_query, (item_id, username))
        
        
    def delete_user(self, username: str):
        """Delete all rows from the database where user_id is the same as specified"""
        
        
        # If this user does not exists, then terminate the function
        if username not in self.get_usernames():
            return None
        
        # DELETE all rows from user_selections with the username as the order_id
        query = """
            DELETE FROM user_selections
            WHERE user_id = ?
        """
        with sqlite3.connect(DATABASE_FILE) as conn:
            conn.execute(query, (username, ))
            
    
    def show_user_df(self):
        """
        Convert the user_selections table from the database format with columns [item_id, user_id, selection] to a 
        format which designates a column for each user().
        """
        
        # Get the current database table as a dataframe
        db_table = self._read_current_user_selections()
        
        # Pivot the dataframe such that each user_id gets a column
        pivoted_df = db_table.pivot(index='item_id', columns='user_id', values='selection')
        
        # Initialize an item_id column
        item_ids = pivoted_df.index.to_list()
        user_df = pd.DataFrame({'item_id': item_ids})
        
        # Add a new column for each user
        for username in pivoted_df.columns:
            # Pivoted_df still has index as item_id. Drop and replace this for consistency with user_df
            user_df[username] = pivoted_df[username].reset_index(drop=True).astype(bool)
            
        # Replace item_id by weight, name and price by looking at the database
        OrderData = OrderDataManager()
        items_df = OrderData.load_order_items_by_date(self.order_date)
        
        # If there are user selections, merge the dataframes by item_id, if not just show the order items
        if user_df.empty:
            merged_df = items_df
        else:
            merged_df = pd.merge(items_df, user_df, on='item_id', how='inner')
            
        # Drop the order_id column to be displayed since it is not relevant
        merged_df.drop(columns=['order_id'], inplace=True)

        return merged_df
    
    
    def save_user_df(self, user_df: pd.DataFrame):
        
        # This query updates a specific selection entry given the item_id and the user_id
        update_query = """
            UPDATE user_selections
            SET selection = ?
            WHERE item_id = ? AND user_id = ?
        """
        
        # Change the database entries by changing rows and columns entry by entry.
        # This iterates across every row and column for user_df and update the corresponding entry within the database
        # TODO: change to more efficient methods
        with sqlite3.connect(DATABASE_FILE) as conn:
            # For every row within user_df
            for index, row in user_df.iterrows():
                item_id = row['item_id']

                # For every column of users, obtain their selection
                for user_id in self.get_usernames():
                    # Selection (0 or 1) for the specific uesr_id. This should be a boolean variable (True/False)
                    selection = row[user_id]
                    assert isinstance(selection, (bool))
                    
                    # Execute the update
                    conn.execute(update_query, (int(selection), int(item_id), user_id))
                    conn.commit()
                    