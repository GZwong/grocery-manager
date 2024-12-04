# Third-Party Imports
import numpy as np
import streamlit as st
from pandas import DataFrame, isna
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode, AgGridTheme

# Project-Specific Imports
import frontend.api_client as api

class ReceiptEditor:
    
    """
    Initialize a ReceiptEditor class using receipt data and user-quantity data
    and render two AG grids to display the data.
    
    Attributes
    ----------
    self._receipt_id
    
    self._receipt_df
    
    self._user_df
    
    Inputs
    ------
    receipt_df
        A pandas DataFrame with columns containing item information, with
        columns: "item_id", "item_name", "quantity", "weight"
    user_df
        A pandas Dataframe storing user item association, with columns:
        "item_id", "user_id", "unit"
    name_id_map:
        A dictionary mapping a user_id to a username, e.g.
        {1: 'Thomas', 2: 'Tommy'}
        
    Methods
    -------
    
    """
    
    def __init__(self, receipt_id:int):
        
        self._receipt_id = receipt_id
        self._fetch_receipt_data()
        self._validate_columns()
        self._column_defs = self._create_column_def()
        
        # Initialize user information
        self.user_ids = []
        self.usernames = []
        self.no_users = []
        
        # Merge the receipt data with user data (if applicable)
        self._df = self._pivot_and_merge()
                
        # Render both grids
        self._render_receipt_grid()
        if hasattr(self, '_user_df'):
            self._render_user_cost()  

  
    def _fetch_receipt_data(self):
        # Query receipt data using receipt ID
        self._receipt_data: list[dict] = api.get_receipt_data(self._receipt_id)
        if self._receipt_data:
            
            # Store the receipt data in a dataframe
            self._receipt_df = DataFrame(self._receipt_data)
            
            # Check and update for users associated with this receipt
            self._fetch_user_info_update()

        
    def _validate_columns(self):
        """Ensure all columns cohere to expected format"""
        
        # Column names assertion
        assert 'item_id'  in self._receipt_df.columns
        assert 'item_name'     in self._receipt_df.columns
        assert 'price'    in self._receipt_df.columns
        assert 'quantity' in self._receipt_df.columns
        assert 'weight'   in self._receipt_df.columns
        
        # Replace None with 0 to ensure pandas do not omit it
        self._receipt_df  = self._receipt_df.fillna({'quantity': 0, 'weight': 0})
        
        
        if hasattr(self, '_user_df'):
            
            # Assert column names if there are previous user data
            assert 'item_id'  in self._user_df
            assert 'unit' in self._user_df
            
            # Replace None with zeros ot ensure pandas do not omit it
            self._user_df = self._user_df.fillna({'unit': 0})
        
        # Add a 'no_units' column for calculating user price later. This takes
        # quantity or weight, whichever that is not none
        self._receipt_df['no_units'] = np.where(self._receipt_df['quantity'] == 0, self._receipt_df['weight'], self._receipt_df['quantity'])


    def _pivot_and_merge(self):
        """
        Merge the dataframe containing receipt data of items with the dataframe
        containing relationship data between items and users.
        """
        # Check if user data is given, abort merge if not
        if not hasattr(self, '_user_df'):
            return self._receipt_df
        
        # Merge user data with corresponding items of the receipt using item ID
        pivot_df = self._user_df.pivot_table(index='item_id', columns='user_id', values='unit')
        pivot_df.reset_index(inplace=True)
        pivot_df.columns = pivot_df.columns.astype(str)
        return self._receipt_df.merge(pivot_df, on='item_id', how='outer')
    
    
    def _create_column_def(self):
        """Create column definitions for the AG grid."""
        
        column_def = []
        
        # Define numeric columns for user
        if hasattr(self, '_user_df'):
            for id, name in zip(self.user_ids, self.usernames):
                column_def.append({
                    "headerName": str(name), 
                    "field": str(id), 
                    "editable": True, 
                    "type": "numericColumn",
                })

        # Define non-editable columns and headers for the rest
        column_def.extend([
            {"headerName": "Name", "field": "item_name", "editable": False},
            {"headerName": "Price [£]", "field": "price", "editable": False},
            {"headerName": "Quantity", "field": "quantity", "editable": False},
            {"headerName": "Weight [kg]", "field": "weight", "editable": False},
            {"headerName": "Item ID", "field": "item_id", "editable": False, "hide": True}
        ])
        
        return column_def
    

    def _render_receipt_grid(self):
        
        grid_options = GridOptionsBuilder.from_dataframe(self._df)
        
        # Create the custom JavaScript function for setting min and max based on adjacent 'no_units' field
        cellEditorParams_code = JsCode("""
            function(params) {
                // Retrieve the value from the adjacent 'no_units' field
                var maxVal = params.data['no_units'];
                return {
                    min: 0,
                    max: maxVal !== null ? maxVal : 0  // Set to Infinity if no_units is null
                };
            }
        """)

        # Adding the column definitions to grid options
        for col in self._column_defs:
            # Default configuration for our columns
            grid_options.configure_column(col["field"], headerName=col["headerName"], editable=col["editable"], type=col.get("type", None))
            # Further configure the minimum value
            if col['field'] not in ['item_id', 'item_name', 'price', 'quantity', 'weight']:
                grid_options.configure_column(col['field'], headerName=col["headerName"], cellEditorParams=cellEditorParams_code)
        
        # Hide item_id, no_units and price columns
        grid_options.configure_column("item_id", hide=True)
        grid_options.configure_column("no_units", hide=True)
        
        # Build grid options
        grid_options = grid_options.build()

        # Render the grid
        self._receipt_grid = AgGrid(
            self._df,
            gridOptions=grid_options,
            enable_enterprise_modules=False,
            update_mode=GridUpdateMode.VALUE_CHANGED,
            data_return_mode='AS_INPUT',
            allow_unsafe_jscode=True,
            theme=AgGridTheme.ALPINE,
        )
        
        
    def _render_user_cost(self):
        
        # Calculate costs using most updated data
        self._fetch_user_info_update()
        updated_df: DataFrame = self._receipt_grid['data']
        
        # Initialize array to store user costs
        self._user_cost: list = [0 for i in range(self.no_users)]
        
        # Calculate user cost and update array
        for idx, row in updated_df.iterrows():
            # Determine if weight or quantity used as units
            price_per_unit = float(row['price'])/row['no_units']
            # Calculate cost per user
            for i, id in enumerate(self.user_ids):
                self._user_cost[i] += float(row[str(id)] * price_per_unit)
   
        # Render the cost grid
        col1, col2 = st.columns([3, 1])
        
        # Column 1: User Cost 
        with col1:
            columns = st.columns(len(self.user_ids))
            for col, username, cost in zip(columns, self.usernames, self._user_cost):
                with col:
                    st.metric(f"{username}", f"£{cost:.2f}")

        # Column 3: Submit Button
        with col2:
            if st.button("Submit Changes"):
                status = self._save_changes()
                if status:
                    st.success("Updated successfully!")
                else:
                    st.error("An error has occured. Try again.")


    def _fetch_user_info_update(self):
        """
        Fetch latest user information (e.g., who is part of this receipt) and
        save under object attributes. 
        
        Return True if user information are found, False if not.
        """
        # Check if there are users associated with this receipt already
        user_items_association = api.get_users_items_in(self._receipt_id)
            
        # If there are previous records of users associated with this 
        # receipt, combine it with item data
        if user_items_association:
            # Store the available usernames and user IDs as separate lists
            # Intermediate conversion to a set to retain unique values 
            self.user_ids  = list(set([user_item['user_id'] 
                                        for user_item in user_items_association]))
            self.usernames = [api.get_username(id) for id in self.user_ids]
            self.no_users = len(self.user_ids)
                
            # Store user spending per item in a dataframe
            self._user_df = DataFrame(user_items_association)
            
            return True
        
        return False


    def _save_changes(self):
        
        # Obtain the latest data from the user-updated grid
        updated_df = self._receipt_grid['data']

        # Prepare empty lists to store updated entries
        user_ids = []
        item_ids = []
        units    = []

        # Loop across every user
        for id in self.user_ids:

            # Filter to the item name, item ID and user columns
            filtered_df = updated_df.loc[:, [str(id), 'item_id']]
            for _, row in filtered_df.iterrows():
                
                # Included explicit type conversion to ensure compatibility
                # with database
                user_ids.append(int(id))
                item_ids.append(int(row['item_id']))
                # Need to specify a string representation of the ID
                units.append(float(0 if isna(row[str(id)]) else row[str(id)]))

        # Save changes to database
        api.update_user_item_association(user_ids, item_ids, units)
        api.update_user_spending(self._receipt_id, 
                                 self.user_ids,
                                 self._user_cost)
        
        return True

