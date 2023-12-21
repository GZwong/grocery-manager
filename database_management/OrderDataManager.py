# Standard Imports
import sqlite3
import pandas as pd
from datetime import datetime
from typing import Union

# Project-specific Imports
from path_management.base import get_database_path
from src.ReceiptClasses.SainsburysReceipt import SainsburysReceipt


# Absolute Path to the sqlite3 database
DATABASE_FILE = get_database_path()


class OrderDataManager():
    """
    Class to manipulate "order_info" and "order_items" tables.
    
    Attributes
    ----------
    No attributes
    
    Methods
    -------
    _create_order_tables(self)
        (PRIVATE) Create two tables "order_info" and "order_items" within the database.
        
    check_if_date_exist(self, date: datetime)
        (PUBLIC) Get dataframe of order dates
        
    get_all_dates(self)
        (PUBLIC) Get all order dates available in the database
    
    upload_order(self, receipt: SainsburysReceipt)
        (PUBLIC) Insert the order information into "order_info" and "order_items"
         
    delete_order_by_date(self, receipt: Sainsburys Receipt)
        (PUBLIC) Given an order date, delete all relevant information from "order_info" and "order_items"

    """
    
    def __init__(self):
        
        # Create order tables IF NOT EXISTS
        self._create_order_tables()
        
    
    # DATABASE MANAGEMENT
    # -------------------------------------------------------------------------- 
    def _create_order_tables(self):
        """Create two tables "order_info" and "order_items" to store all information regarding the order."""

        with sqlite3.connect(DATABASE_FILE) as conn:
            # Enable foreign key support
            conn.execute("PRAGMA foreign_keys = ON;")

            # Create "order_info" as the PARENT TABLE
            conn.execute('''
                CREATE TABLE IF NOT EXISTS order_info(
                    order_id INTEGER PRIMARY KEY,
                    order_date DATE
                )               
            ''')
            # Create "order_items" as the CHILD TABLE
            # Define foreign key with CASCADING DELETE so that deleting a particular order_date from "order_info"
            # will delete all associated order_id from "order_items"
            conn.execute('''
                CREATE TABLE IF NOT EXISTS order_items(
                    item_id INTEGER PRIMARY KEY,
                    order_id INTEGER,
                    weight TEXT,
                    item_name TEXT,
                    price REAL,
                    FOREIGN KEY (order_id) REFERENCES order_info(order_id)
                    ON DELETE CASCADE
                )    
            ''')
        return None
    
    
    def check_if_date_exists(self, date: datetime) -> bool:
        """Return 1 if this date exists within the database, return 0 if not."""
        
        query = "SELECT COUNT(*) FROM order_info WHERE order_date = ?;"
        with sqlite3.connect(DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (date,))
            # "result" is a tuple with a count of how many times this order_date appeared
            result = cursor.fetchone()

        if result[0] > 0:
            print(f"The date '{date}' exists in the order_info table.")
            return 1
        print(f"The date '{date} does not exist in the 'order-info' table.")
        return 0
    
    
    def get_all_dates(self) -> pd.DataFrame:
        """Return a dataframe of a single column containing all "order_date" in the database"""
        query = "SELECT order_date from order_info"
        with sqlite3.connect(DATABASE_FILE) as conn:
            order_dates = pd.read_sql_query(query, conn)
        return order_dates


    def upload_order(self, receipt: SainsburysReceipt):
        """Upload the receipt information to the database, pertaining the two tables (order_info and order_items)"""
        
        # Extract information from pdf and prepare as dataframes to utilize pd.to_sql()    
        # Convert order_date to string for readability
        order_date_str = datetime.strftime(receipt.order_time, '%Y-%m-%d %H:%M:%S')    
        info_df = pd.DataFrame({'order_id': [receipt.order_id],
                                'order_date': [order_date_str]})
        item_df = pd.DataFrame(receipt.get_item_list())
                
        # If date exists already, terminate the function
        if self.check_if_date_exists(order_date_str):
            return "This is already available within the database."
        
        # Append this data as new rows
        with sqlite3.connect(DATABASE_FILE) as conn: 
            info_df.to_sql('order_info', conn, if_exists='append', index=False)
            item_df.to_sql('order_items', conn, if_exists='append', index=False)
        
        return "Data uploaded to database"
    
    
    def delete_order_by_date(self, order_date: datetime):
        """Delete all rows related to the order_date from both tables (order_info and order_items)"""
        
        # Ensure order_date is in proper string format since it is what's stored in the database 
        if isinstance(order_date, datetime):
            order_date = datetime.strftime(order_date, "%Y-%m-%d %H:%M:%S")
            
        # Delete from parent table "order_info" and allow it to cascade down to "order_items"
        delete_query = "DELETE FROM order_info WHERE order_date = ?"
        with sqlite3.connect(DATABASE_FILE) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")  # Enable foreign key support
            conn.execute(delete_query, (order_date, ))


    def load_order_items_by_date(self, order_date: Union[datetime, str]) -> pd.DataFrame:
        """
        Return a dataframe corresponding to the "order_items" table in the
        database, filtered to the input date.
        """
        query = """
            SELECT * FROM order_items AS items
            WHERE items.order_id IN (
                SELECT info.order_id FROM order_info AS info
                WHERE info.order_date = ?
            )
        """
        with sqlite3.connect(DATABASE_FILE) as conn:
            df = pd.read_sql_query(query, conn, params=[order_date, ])
        return df
            