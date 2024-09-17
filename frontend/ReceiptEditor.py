# Third-Party Imports
import numpy as np
import streamlit as st
from pandas import Series, DataFrame, isna, concat, notnull
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode, AgGridTheme

# Project-Specific Imports
from utils import update_user_item_association

class ReceiptEditor:
    
    """
    Initialize a ReceiptEditor class using receipt data and user-quantity data
    and render two AG grids to display the data.
    
    Inputs
    ------
    receipt_df
        A pandas DataFrame with columns containing item information, with
        columns: "item_id", "item_name", "quantity", "weight"
    user_df
        A pandas Dataframe storing user item association, with columns:
        "item_id", "user_id", "quantity" and "weight"
    name_id_map:
        A dictionary mapping a user_id to a username, e.g.
        {1: 'Thomas', 2: 'Tommy'}
        
    Methods
    -------
    
    """
    
    def __init__(self, receipt_df: DataFrame, user_df: DataFrame = DataFrame(), name_id_map: dict = dict()):
        
        self._receipt_df  = receipt_df
        self._user_df = user_df
        self._id_name_map = name_id_map
        
        self._get_user_ids()
        self._validate_columns()
        self._column_defs = self._create_column_def()
        
        self._df = self._pivot_and_merge()
                
        # Render both grids
        self._render_receipt_grid()
        if not user_df.empty:
            self._render_user_cost_grid()  

    def _get_user_ids(self):
        """Get a list of user IDs as an attribute"""
        if not self._user_df.empty:
            self._user_ids: list[int] = self._user_df['user_id'].unique()
        
    def _validate_columns(self):
        """Ensure all columns cohere to expected format"""
        
        # Column names assertion
        assert 'item_id'  in self._receipt_df.columns
        assert 'name'     in self._receipt_df.columns
        assert 'price'    in self._receipt_df.columns
        assert 'quantity' in self._receipt_df.columns
        assert 'weight'   in self._receipt_df.columns
        
        if not self._user_df.empty:
            assert 'item_id'  in self._user_df
            assert 'quantity' in self._user_df
        
        # Replace None with 0 to ensure pandas do not omit it
        self._receipt_df  = self._receipt_df.fillna({'quantity': 0, 'weight': 0})
        self._user_df = self._user_df.fillna({'quantity': 0, 'weight': 0})
        
        # Add a 'no_units' column for calculating user price later. This takes
        # quantity or weight, whichever that is not none
        self._receipt_df['no_units'] = np.where(self._receipt_df['quantity'] == 0, self._receipt_df['weight'], self._receipt_df['quantity'])


    def _pivot_and_merge(self):
        """
        Merge the dataframe containing receipt data of items with the dataframe
        containing relationship data between items and users.
        """
        # Check if user data is given, abort merge if not
        if self._user_df.empty:
            return self._receipt_df
        
        # Merge user data with corresponding items of the receipt using item ID
        pivot_df = self._user_df.pivot_table(index='item_id', columns='user_id', values='quantity')  # if values are put in a list, it becomes a multilevel dataframe
        pivot_df.reset_index(inplace=True)
        pivot_df.columns = pivot_df.columns.astype(str)
        return self._receipt_df.merge(pivot_df, on='item_id', how='outer')
    
    
    def _create_column_def(self):
        
        column_def = []
        
        # Define numeric columns for user
        if not self._user_df.empty:
            for id, name in self._id_name_map.items():
                column_def.append({
                    "headerName": str(name), 
                    "field": str(id), 
                    "editable": True, 
                    "type": "numericColumn",
                })

        # Define non-editable columns and headers for the rest
        column_def.extend([
            {"headerName": "Name", "field": "name", "editable": False},
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
            if col['field'] not in ['item_id', 'name', 'price', 'quantity', 'weight']:
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
        
        
    def _render_user_cost_grid(self):
        
        # Calculate using most updated data
        updated_df: DataFrame = self._receipt_grid['data']
        
        # Initialize dictionary to store user costs
        user_cost: dict = dict((id, 0) for id in self._user_ids)
        
        # Calculate user cost and update dictionary
        for idx, row in updated_df.iterrows():
            # Determine if weight or quantity used as units
            price_per_unit = float(row['price'])/row['no_units']
            # Calculate cost per user
            for id in self._user_ids:
                user_cost[id] += row[str(id)] * price_per_unit
                
        # Construct a dataframe based on the cost data
        cost_df: DataFrame = DataFrame([user_cost])  # Wrap within a list to represent a row
        
        # Display cost as two decimal places
        cost_df[list(self._id_name_map.keys())]\
            = cost_df[list(self._id_name_map.keys())].\
                map(lambda x: f"{x:.2f}" if notnull(x) else "")
                
        # AG Grid requires column names to be str
        cost_df.columns = cost_df.columns.astype(str)
        
        # Configure display name for users
        column_def: list[dict] = []
        for id, name in self._id_name_map.items():
            column_def.append({
                "headerName": str(name), 
                "field": str(id), 
                "editable": False, 
                "type": "numericColumn",
            })

        # Build grid options based on column definition
        grid_options = GridOptionsBuilder.from_dataframe(cost_df)
        for col in column_def:
            grid_options.configure_column(col["field"], 
                                          headerName=col["headerName"], 
                                          editable=col["editable"], 
                                          type=col.get("type", None))
        grid_options = grid_options.build()
        
        # Render the cost grid
        col1, col2, col3 = st.columns([1, 3, 1])
        
        #   Column 1: Total Price Header
        with col1:
            col1.subheader("Total Price [£]")

        #   Column 2: User Cost 
        with col2:
            self._user_cost_grid = AgGrid(
                cost_df,
                gridOptions=grid_options,
                enable_enterprise_modules=False,
                update_mode=GridUpdateMode.VALUE_CHANGED,
                theme=AgGridTheme.ALPINE,
                height=100, 
            )

        # Column 3: Submit Button
        with col3:
            if st.button("Submit Changes"):
                status = self._save_changes()
                if status:
                    st.success("Updated successfully!")


    def _save_changes(self):
        
        updated_df = self._receipt_grid['data']

        # Prepare a dictionary to store updated entries
        # First update user-item association
        updated_user_item_association = {'user_items': []}
        # Loop across every user
        for id in self._user_ids:
            filtered_df = updated_df.loc[:, [str(id), 'name', 'item_id', 'weight']]
            for _, row in filtered_df.iterrows():
                
                # Do not save the "total_price" row
                if row['name'] == "Total Price [£]":
                    continue
                
                # Save for all other rows
                updated_user_item_association['user_items'].append(
                    {'user_id': int(id),
                    'item_id': int(row['item_id']),
                    'quantity': 0 if isna(row[str(id)]) else row[str(id)],
                    'weight': 0 if isna(row['weight']) else row ['weight']}
                )

        # TODO: Then update user costs

        # Save changes to database
        update_user_item_association(updated_user_item_association)
        
        return True
