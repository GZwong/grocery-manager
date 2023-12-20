import pandas as pd
from datetime import datetime as dt
from pypdf import PdfReader

# Project-specific Imports
from src.ReceiptClasses import Receipt

# TODO: Create another Receipt class to be inherited (in case of other receipts)

class SainsburysReceipt(Receipt):
    
    def __init__(self, pdf_file):

        self._file = pdf_file
        
        self._content = None           # A list of PDF lines (Raw)
        self._order_id = None          # Order ID
        self._order_date = None        # Order Date
        self._item_dict = None         # List of dictionaries containing info for each item

        self._parse_receipt()
        # Order ID and time
        self._find_order_id_time()
        # Order Items
        self._find_items_info()
  
  
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
        order_date, order_hours = order_time.split(',')
        # Further split the date information into day, date, month and year
        day, date, month, year = order_date.split()
        # Remove the suffixes from order_date by removing last two characters (st, nd, rd, th)
        date = date[:-2]
        # Rejoin the date information into a single string, then convert it into a datetime object
        order_date = f"{day} {date} {month} {year}"
        order_date = dt.strptime(order_date, r'%A %d %B %Y')
        
        # Save permanently as attributes
        self._order_id = order_id
        self._order_date = order_date

    def _find_items_info(self):
        """
        Decouple each item into its "Name", "Quantity", "Weight" and "Price",
        then store them as a list of dictionaries.

        Implementation Logic:
            1. The "amount" of an item is either:
                - Quantity
                - Weight
            2. Item name starts with a capital letter. This works most of the time since quantities are
            numeric, sometimes with lowercase units such as kg, g etc.
            3. Prices are the numeric values occuring after £
            4. For long orders (multi-lines) check whether the £ symbol appears. If it does not, append it to the next line
        """

        # Filter content to information on the orders only
        for index, line in enumerate(self._content):
            if line.startswith("Delivery summary"):
                start_index = index
            elif line.startswith("Order summary"):
                end_index = index
        
        filtered_content = self._content[start_index + 1: end_index]

        # Initialize lists
        previous_line = ''         # In case a single item spans multiple rows. See logic below.
        previous_line_length = 0   # To adjust pound index in case of multi-line rows
        
        for order in filtered_content:

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
                amount = order[: item_index]
                name = order[item_index: pound_index - 1]
                price = order[pound_index + 1:]
            
                # Amount can either be quantity or weight. Store it as 'weight' if it ends with 'kg'.
                # TODO: Add other units in the future.
                if amount.endswith("kg"):
                    weight = amount
                    quantity = None
                else:
                    weight = None
                    quantity = amount

                # Append information to the list of dictionaries
                self._item_dict.append(
                    {
                        "Name": name,
                        "Quantity": int(quantity),
                        "Weight": weight,
                        "Price": float(price)
                    }
                )
    
    @property
    def order_id(self):
        return self._order_id
    
    @property
    def order_date(self):
        return self._order_date
    
    @property
    def items(self):
        return self._item_dict
    