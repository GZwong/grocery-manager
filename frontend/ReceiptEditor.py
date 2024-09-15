from pandas import DataFrame, isna
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

from utils import update_user_item_association

class ReceiptEditor:
    
    """
    Initialize a ReceiptEditor class.
    
    Stores an internal dataframe that corresponds to the column names for the
    database, and an external (display) dataframe to show to frontend
    
    Inputs
    ------
    item_df
        A pandas DataFrame with columns containing item information, with
        columns: "item_id", "item_name", "quantity", "weight"
    user_items_df
        A pandas Dataframe storing user item association, with columns:
        "item_id", "user_id", "quantity" and "weight"
    name_id_map:
        A dictionary mapping a user_id to a username, e.g.
        {1: 'Thomas', 2: 'Tommy'}
        
    Methods
    -------
    
    """
    
    def __init__(self, item_df: DataFrame, user_items_df: DataFrame, name_id_map: dict):
        
        self._item_df = item_df
        self._user_items_df = user_items_df
        self._user_map = name_id_map
        
        self._validate_columns()
        self._get_user_ids()
        self._internal_df = self._pivot_and_merge()
        self._display_df = self._internal_df.copy(deep=True)
        self._display_df = self._translate_column_name_to(self._display_df, "display")
        self._gb = GridOptionsBuilder.from_dataframe(self._display_df)
        self._configure_numeric_column()
        
    def _get_user_ids(self):
        self._user_ids = self._user_items_df['user_id'].unique()
        
    def _validate_columns(self):
        """Ensure all columns cohere to expected format"""
        assert 'item_id' in self._item_df
        assert 'name' in self._item_df.columns
        assert 'price' in self._item_df.columns
        assert 'quantity' in self._item_df.columns
        
        assert 'item_id' in self._user_items_df
        assert 'quantity' in self._user_items_df
        # assert 'weight' in self._user_items_df
        
    def _pivot_and_merge(self):
        """
        Merge the dataframe containing receipt data of items with the dataframe
        containing relationship data between items and users.
        """
        
        # Replace None with 0 to ensure pandas do not omit it
        self._user_items_df = self._user_items_df.fillna({'quantity': 0, 'weight': 0})
        
        # Merge user data with corresponding items of the receipt using item ID
        pivot_df = self._user_items_df.pivot_table(index='item_id', columns='user_id', values='quantity')  # if values are put in a list, it becomes a multilevel dataframe
        pivot_df.reset_index(inplace=True)
        return self._item_df.merge(pivot_df, on='item_id', how='outer') 
        
    def _translate_column_name_to(self, df: DataFrame, format:str='display'):
        """Change the column name between the internal and display name"""
        int2disp_map = {"name": "Name", "quantity": "Quantity", "weight": "Weight [kg]"}
        int2disp_map.update(self._user_map)
        disp2int_map = dict((v, k) for k, v in int2disp_map.items())
        
        if format == 'display':
            df.rename(columns=int2disp_map, inplace=True)
        elif format == 'internal':
            df.rename(columns=disp2int_map, inplace=True)
            
        # Convert the displayed columns to string so that it can be worked by AgGrid
        df.columns = df.columns.astype(str)
        return df
            
    def _configure_numeric_column(self, col_name=None):
        # Find the user columns to editable
        for col_name in self._display_df.columns:
            # Translate the columns that are not 'item_id', 'name' and 'quantity'
            if col_name not in ['item_id', 'name', 'price', 'quantity', 'weight']:
                self._gb.configure_column(col_name, editable=True, type=['numericColumns'], cellEditor="agNumberCellEditor")

    def render_grid(self):
        
        grid_options = self._gb.build()
        self._grid = AgGrid(
            self._display_df,
            gridOptions=grid_options,
            enable_enterprise_modules=False,
            update_mode=GridUpdateMode.VALUE_CHANGED,
            data_return_mode='AS_INPUT'
        )
        return self._grid
    
    def save_changes(self):
        
        updated_df = self._grid['data']
        # Switch column names back from display to internal
        updated_df = self._translate_column_name_to(df=updated_df, format='internal')

        # Prepare a dictionary to store updated entries
        updated_user_item_association = {'user_items': []}
        # Loop across every user
        for id in self._user_ids:
            filtered_df = updated_df.loc[:, [str(id), 'item_id', 'weight']]
            for _, row in filtered_df.iterrows():
                updated_user_item_association['user_items'].append(
                    {'user_id': int(id),
                    'item_id': int(row['item_id']),
                    'quantity': 0 if isna(row[str(id)]) else row[str(id)],
                    'weight': 0 if isna(row['weight']) else row ['weight']}
                )
        print(updated_user_item_association)
        # Save changes to database
        print("Updating database...")
        update_user_item_association(updated_user_item_association)
        
        return True
        