from datetime import datetime as dt
from pypdf import PdfReader
from typing import List, Dict, Union

# Project-specific Imports
from src.ReceiptClasses.Receipt import Receipt


class SainsburysReceipt(Receipt):
    
    def __init__(self, pdf_file: str):
        """Initialize a SainsburysReceipt object.

        Args:
            pdf_file (str): Path to the receipt PDF file.
        """
        # Parent Class Initialization
        super().__init__(pdf_file)

        # List of raw PDF lines
        self._raw_content = self._parse_receipt(pdf_file)
        
        # Order ID, time and items
        self._order_id = self._find_order_id()
        self._order_time = self._find_order_time()
        self._item_dict = self._find_items_dict()
  

    def _parse_receipt(self, pdf_file: str):
        """
        Uses the PdfReader module to read and parse the receipts pdf into a list, each element
        representing a line in the receipt.
        """
        reader = PdfReader(pdf_file)

        pdf_content = []
        for page in reader.pages:
            text = page.extract_text()  # This returns a single string of everything on the pdf
            lines = text.split("\n")    # This creates a list for each line
            pdf_content.extend(lines)   # Extend it to the pdf_content list
        return pdf_content


    def _find_order_id(self) -> int:
        """
        Find the unique order ID by browsing through its content.
        """

        for line in self._raw_content:
            
            # Look for order ID by splitting by colon ":"
            if line.startswith("Your receipt for order: "):
                _, order_id = line.split(':')  # Split into ["Your receipt for order:", order_id] 
                order_id = order_id.strip()    # Use strip to remove any leading/trailing whitespace
                break

        order_id = int(order_id)  # Ensure type consistency

        return order_id

        
    def _find_order_time(self) -> dt:
        """
        Find the order time by browsing through its content.
        """

        # The time contains multiple colons. Therefore we look for the first colon only.
        for line in self._raw_content:
            
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
        
        return order_date


    def _find_items_dict(self) -> Dict[str, Dict[str, Union[int, float]]]:
        """
        Store a nested dictionary into self._item_dict in the form:

        {
            "Item1": {"Quantity": 1, "Weight": 0.708kg, "Price": 4.00}.
            "Item2": {"Quantity": 3, "Weight":    None, "Price": 2.99}
        }

        Implementation Logic:
            1. The "amount" of an item is either:
                - Quantity
                - Weight
            2. Item name starts with a capital letter. This works most of the time since quantities are
            numeric, sometimes with lowercase units such as kg, g etc.
            3. Prices are the numeric values occuring after £
            4. For long orders (multi-lines) check whether the £ symbol appears. If it does not, append it to the next line
        """
        # Empty dictionary to store items
        item_dict = {}

        # Filter content to information on the orders only
        for index, line in enumerate(self._raw_content):
            if line.startswith("Delivery summary"):
                start_index = index
            elif line.startswith("Order summary"):
                end_index = index
        
        filtered_content = self._raw_content[start_index + 1: end_index]

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
                if amount.endswith("kg"):
                    amount = amount[:-2]   # Strip away "kg"
                    weight = float(amount)
                    quantity = 1
                else:
                    weight = None
                    quantity = int(amount)

                price = float(price)

            # Store items as a list of dictionaries
            item_dict[name] = {"Quantity": quantity, "Weight": weight, "Price": price}

        return item_dict
    

    def get_item_list(self) -> List[Dict]:
        """
        Returns a list of dictionaries where each entry correspond strictly to a
        single item - items with more than quantity will be duplicated in the
        list.

        Returns:
            List[Dict]:
                A list of dictionaries where each item correspond to an entry.
        """

        item_list = []

        # Convert nested dictionary to a list of dictionaries
        for item_name, attributes in self._item_dict.items():
            
            quantity = attributes["Quantity"]
            weight = attributes["Weight"]
            price = attributes["Price"]

            for i in range(quantity):
                row = {"item_name": item_name,
                        "weight": weight,
                        "price": price/quantity,  # Divide evenly among items
                        "order_id": self.order_id
                        }
                item_list.append(row)
            
        return item_list


    # Getters ------------------------------------------------------------------
    @property
    def order_id(self) -> int:
        return self._order_id
    
    @property
    def order_time(self) -> dt:
        return self._order_time

    @property
    def order_items(self) -> Dict[str, Dict[str, Union[int, float]]]:
        """Returns a nested dictionary of the receipt items.

        Returns:
            Dict[str, Dict[str, Union[int, float]]]:
                Nested dictionary of order items, with item names as the keys.
                For example:

                {
                    "Item1": {"Quantity": 1, "Weight": 0.708kg, "Price": 4.00}.
                    "Item2": {"Quantity": 3, "Weight":    None, "Price": 2.99}
                }
        """
        return self._item_dict
