from abc import ABC, abstractmethod
from datetime import datetime as dt
from typing import Dict, Union, List

class Receipt(ABC):
    """
    Abstract base class for parsing different types of receipts.

    This class provides a common interface and basic structure for receipt objects.
    Subclasses should implement the abstract methods to handle specific formats and details
    of each type of receipt.

    Attributes:
        _raw_content (List[str]): Raw text content of the receipt, line by line.
        _order_id (int): Identifier for the order.
        _order_date (dt): Date and time of the order.
        _item_dict (Dict[str, Dict[str, Union[int, float]]]): Dictionary containing item details.
    """

    def __init__(self, pdf_file: str):
        """
        Initializes the Receipt object with a file path.

        Args:
            pdf_file (str): Path to the receipt PDF file.
        """
        self._raw_content = self._parse_receipt(pdf_file)
        self._order_id = self._find_order_id()
        self._order_time = self._find_order_time()
        self._item_dict = self._find_items_info()

    @abstractmethod
    def _parse_receipt(self, pdf_file: str) -> List[str]:
        """
        Parses the receipt file into a list of strings.

        Each subclass should provide its own implementation to handle the
        specific format of the receipt.

        Args:
            pdf_file (str): Path to the receipt PDF file.

        Returns:
            List[str]: List of strings, each representing a line in the receipt.
        """
        pass

    @abstractmethod
    def _find_order_id(self) -> int:
        """
        Abstract method to extract the order ID from the receipt.

        Each subclass should provide its own implementation based on the receipt's layout.

        Returns:
            int: The order ID.
        """
        pass

    @abstractmethod
    def _find_order_time(self) -> dt:
        """
        Abstract method to extract the order time from the receipt.

        Each subclass should provide its own implementation based on the receipt's layout.

        Returns:
            dt: The date and time of the order.
        """
        pass

    @abstractmethod
    def _find_items_info(self) -> Dict[str, Dict[str, Union[int, float]]]:
        """
        Abstract method to extract item information from the receipt.

        Each subclass should implement this method to parse details about the items,
        such as name, quantity, weight, and price.

        Returns:
            Dict[str, Dict[str, Union[int, float]]]: Nested dictionary of item details.
        """
        pass

    # Getters ------------------------------------------------------------------
    @property
    def order_id(self) -> int:
        return self._order_id
    
    @property
    def order_date(self) -> dt:
        return self._order_date
    
    @property
    def items(self) -> Dict[str, Dict[str, Union[int, float]]]:
        return self._item_dict
