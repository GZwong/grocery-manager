"""
This script contains the main class for parsing and storing data of a Sainsbury
receipt.

This file can be ran to verify the parsing logic.
"""
import argparse
import pandas as pd
from datetime import datetime as dt
from pypdf import PdfReader

# Project-Specific Imports
from path_management.base import get_base_path

# TODO: Create another Receipt class to be inherited (in case of other receipts)

class SainsburysReceipt():
    
    def __init__(self, pdf_file):

        self._file = pdf_file
        
        self._content = None           # A list of PDF lines (Raw)
        self._filtered_content = None  # A list of strings for items
        self._order_id = None          # Order ID
        self._order_date = None        # Order Date
        self._quantities = None        # List of quantities for each item
        self._weights = None           # List of weights for each item
        self._names = None             # List of names for each item
        self._prices = None            # List of prices for each item

        self._item_df = None           # Pandas Dataframe of all orders
        
        self._parse_receipt()
        # Order ID and time
        self._find_order_id_time()
        # Order Items
        self._filter_content_to_items()
        self._find_items_info()
        self._process_item_info()
  
    def _parse_receipt(self):
        """
        Uses the PdfReader module to read and parse the receipts pdf into a list, each element
        representing a line in the receipt.
        """
        reader = PdfReader(self._file)

        pdf_content = []
        for page in reader.pages:
            text = page.extract_text()  # This returns a single string of everything on the pdf
            lines = text.split("\n")    # This creates a list for each line
            pdf_content.extend(lines)   # Extend it to the pdf_content list
        self._content = pdf_content
        

    def _find_order_id_time(self):
        """
        Uses the PdfReader module to read and parse the receipts pdf into a list, each element
        representing a line in the receipt.
        """
    
        for line in self._content:
            
            # Look for order ID by splitting by colon ":"
            if line.startswith("Your receipt for order: "):
                _, order_id = line.split(':')  # Split into ["Your receipt for order:", order_id] 
                order_id = order_id.strip()    # Use strip to remove any leading/trailing whitespace
            
            # The time contains multiple colons. Therefore we look for the first colon only.
            if line.startswith("Slot time:"):
                first_colon_index = line.index(":")
                order_time = line[first_colon_index + 1:]
                order_time = order_time.strip()  # Use strip to remove any leading/trailing whitespace
                break

        # Convert the date string into a datetime object.
        # ----------
        # Split the time information into a two components [date (Thursday 3rd August 2023), time (9:00pm - 10:00pm)]
        order_date, order_hour = order_time.split(',')
        # Further split the date information into day, date, month and year
        day, date, month, year = order_date.split()
        # Remove the suffixes from order_date by removing last two characters (st, nd, rd, th)
        date = date[:-2]
        # Process the hour data, retaining only the starting time (e.g. 1:00pm - 2:00pm)
        order_hour = order_hour.split(" - ")[0]
        # Rejoin the date information into a single string, then convert it into a datetime object
        order_date = f"{day} {date} {month} {year} {order_hour}"
        order_date = dt.strptime(order_date, r'%A %d %B %Y %I:%M%p')
        
        # Save permanently as attributes
        self._order_id = order_id
        self._order_date = order_date
        

    def _filter_content_to_items(self):
        """
        Remove unnecessary information within the receipt besides the orders. This is located between
        "Delivery summary" and "Order summary".
        """
        # The order starts after the line "Delivery summary" and ends after "Order summary". 
        # Only retain whatever is in between.
        for index, line in enumerate(self._content):
            if line.startswith("Delivery summary"):
                start_index = index
            elif line.startswith("Order summary"):
                end_index = index
        
        self._filtered_content = self._content[start_index + 1: end_index]


    def _find_items_info(self):
        """
        With a filtered list (e.g. returned from find_orders(content_list)), decouple each line into
        the "Quantity", "Item" and "Price" of each Item.

        Logic:
            1. The "amount" of an item is either:
                - Quantity
                - Weight
            2. Item name starts with a capital letter. This works most of the time since quantities are
            numeric, sometimes with lowercase units such as kg, g etc.
            3. Prices are the numeric values occuring after £
            4. For long orders (multi-lines) check whether the £ symbol appears. If it does not, append it to the next line
        """

        # Initialize lists
        quantities = []
        weights = []
        names = []
        prices = []

        previous_line = ''         # In case a single item spans multiple rows. See logic below.
        previous_line_length = 0   # To adjust pound index in case of multi-line rows
        
        for order in self._filtered_content:

            # Find the index of the pound symbol. Everything after this is assumed to be the price.      
            pound_index = order.rfind('£')

            # 1. If there is no pound symbol, pound_index will return -1. If this is the case, save the
            #    current line as a variable named "previous_line". As long as the pound symbol is not found, 
            #    it will keep adding to 'previous_line'.
            # 2. Variable previous_line_length is to readjust for pound_index since the multi-line order
            #    is appended together, so the index where the pound occurs is:
            #               previous_line_length + current_line_pound_index
            if pound_index == -1:
                previous_line = previous_line + order
                previous_line_length = len(order)
                continue   # Skip this loop
            
            # Whenever the pound_symbol is found, reset variables to an empty string to prepare
            # for additional multi-line orders.
            else:
                # Aggregate multi-line order into a single string
                order = previous_line + order
                pound_index = previous_line_length + pound_index
                
                # Reset variables
                previous_line = ''
                previous_line_length = 0
                
                # Analyse each character within the string.
                for index, char in enumerate(order):

                    # Find the index of the item name. Item name is assumed to be the first capital letter 
                    # (units are usually in ml, kg etc. that are not uppercase)
                    if char.isupper():
                        item_index = index
                        break
                
                # Using indices, categorize the information with their respective rows
                amount = order[: item_index].strip()  # .strip to remove whitespace from both sides
                name = order[item_index: pound_index - 1]
                price = order[pound_index + 1:]
                
                # Amount can either be quantity or weight. Store it as 'weight' if it ends with 'kg'.
                # Add other units in the future.
                if amount.endswith("kg"):
                    weight = amount
                    quantity = None
                else:
                    weight = None
                    quantity = int(amount)             # Type conversion here to prevent performing `int(None)``

                # Append to each list
                quantities.append(quantity)            # Quantity stored as integers
                weights.append(weight)                 # Weight stored as strings
                names.append(name)                     # Item names stored as strings
                prices.append(float(price))            # Price stored as floats

        self._quantities = quantities
        self._weights = weights
        self._names = names
        self._prices = prices
    
    
    def _process_item_info(self):
        """
        With the quantities, weights, names and prices of each item, process the data such that each item
        always take one row (an item with a quantity of two will become two items of one quantity each).
        This is to ensure each item can be split separately.
        """
        
        # For rows with a quantity above one (quantity = n), split this into 
        # n rows and divide the price by n to obtain individual prices
        # ----------
        
        # New lists to store the decoupled information
        decoupled_weights = []
        decoupled_items = []
        decoupled_prices = []
        
        for quantity, weight, item, price in zip(self._quantities, self._weights, self._names, self._prices):
            # When quantity exceeds 1, split that order into individual items
            if (quantity) and (quantity > 1):
                decoupled_weights.extend([weight] * quantity)
                decoupled_items.extend([item] * quantity)
                # Prices are summed so these are divided by quantity
                decoupled_prices.extend([price/quantity] * quantity)
            
            # If quantity is one then just append it normally
            else:
                decoupled_weights.append(weight)
                decoupled_items.append(item)
                decoupled_prices.append(price)
                
        # Convert to dataframe as a viewable form
        self._item_df = pd.DataFrame(
            {
                # Append the order_id (which is equal throughout) for referencing other datatables
                'order_id': [self._order_id] * len(decoupled_items),
                'weight': decoupled_weights,
                'item_name': decoupled_items,
                'price': decoupled_prices
            }
        )
    
    
    @property
    def order_id(self):
        return self._order_id
    
    @property
    def order_date(self):
        return self._order_date
    
    @property
    def item_df(self):
        return self._item_df
    
    
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description="PDF file of Sainsbury's receipt")
    parser.add_argument('--file', type=str, required=True, help="The path to the Sainsburys receipt.")
    args = parser.parse_args()
    file_path = args.file
    print(f"The file specified is {file_path}")
    
    Receipt = SainsburysReceipt(file_path)   # TODO: search the file name within the receipts directory
    
    print(f'Order ID:   {Receipt.order_id}')
    print(f"Order date: {Receipt.order_date}")
    print(f"Orders:     {Receipt.item_df}")
    