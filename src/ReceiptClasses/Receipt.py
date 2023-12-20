from abc import ABC, abstractmethod

class Receipt(ABC):
    """
    Abstract base class for parsing different types of receipts.

    This class provides a template for parsing receipts from various sources 
    such as supermarkets or stores. Subclasses should implement the abstract 
    methods to handle specific formats and details of each type of receipt.

    Attributes:
        _file (str): Path to the receipt file.
        _content (list): Parsed content of the receipt, typically a list of lines.
        _order_id (str): Identifier for the order.
        _order_date (datetime): Date of the order.
        _item_dict (list): List of dictionaries containing item details.

    Methods:
        _parse_receipt(): Abstract method to parse the receipt file.
        _find_order_id_time(): Abstract method to extract order ID and time.
        _find_items_info(): Abstract method to extract item information.
    """

    def __init__(self, pdf_file):
        self._file = pdf_file
        self._content = None
        self._order_id = None
        self._order_date = None
        self._item_dict = []

        self._parse_receipt()
        self._find_order_id_time()
        self._find_items_info()

    @abstractmethod
    def _parse_receipt(self):
        """
        Abstract method to parse the receipt.
        This needs to be implemented by each subclass.
        """
        pass

    @abstractmethod
    def _find_order_id_time(self):
        """
        Abstract method to find the order ID and time from the receipt.
        This needs to be implemented by each subclass.
        """
        pass

    @abstractmethod
    def _find_items_info(self):
        """
        Abstract method to extract items information from the receipt.
        This needs to be implemented by each subclass.
        """
        pass

    @property
    def order_id(self):
        return self._order_id
    
    @property
    def order_date(self):
        return self._order_date
    
    @property
    def items(self):
        return self._item_dict
