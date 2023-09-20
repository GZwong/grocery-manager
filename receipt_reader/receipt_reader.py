import pandas as pd
from datetime import datetime as dt
from pypdf import PdfReader   


def parse_receipt(pdf_file):
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


def find_order_id_time(pdf_file):
    
    pdf_content = parse_receipt(pdf_file)
    
    for line in pdf_content:
        
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
    
    return order_id, order_date


def filter_to_orders(pdf_file):
    """
    Remove unnecessary information within the receipt besides the orders. This is located between
    "Delivery summary" and "Order summary".
    """
    # Obtain unfiltered list of pdf content
    content_list = parse_receipt(pdf_file)

    # The order starts after the line "Delivery summary" and ends after "Order summary". 
    # Only retain whatever is in between.
    for index, line in enumerate(content_list):
        if line.startswith("Delivery summary"):
            start_index = index
        elif line.startswith("Order summary"):
            end_index = index
    
    content_list = content_list[start_index + 1: end_index]
    return content_list


def find_orders(pdf_file):
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
    # Obtained filtered list of orders
    order_list = filter_to_orders(pdf_file)

    # Initialize lists
    quantities = []
    weights = []
    names = []
    prices = []

    previous_line = ''         # In case a single item spans multiple rows. See logic below.
    previous_line_length = 0   # To adjust pound index in case of multi-line rows
    
    for order in order_list:

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

    return quantities, weights, names, prices


def process_orders(quantities: list[int], weights: list[str], items: list[str], prices: list[float]):
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
    
    for quantity, weight, item, price in zip(quantities, weights, items, prices):
        # When quantity exceeds 1, split that order into individual items
        # Note that prices are summed so these are divided by quantity
        if quantity > 1:
            decoupled_weights.extend([weight] * quantity)
            decoupled_items.extend([item] * quantity)
            decoupled_prices.extend([price/quantity] * quantity)
        
        # If quantity is one then just append it normally
        else:
            decoupled_weights.append(weight)
            decoupled_items.append(item)
            decoupled_prices.append(price)
            
    # Convert to dataframe as a viewable form
    df = pd.DataFrame(
        {
            'Weights': decoupled_weights,
            'Item': decoupled_items,
            'Price': decoupled_prices
         }
    )

    return decoupled_weights, decoupled_items, decoupled_prices
