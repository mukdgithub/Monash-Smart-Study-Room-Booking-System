"""
Entity class representing a fund transaction in the MSSRB system.
"""


class Transaction:
    """Represents a fund transaction (CREDIT, DEBIT, REFUND)."""

    TYPE_CREDIT = "CREDIT"
    TYPE_DEBIT = "DEBIT"
    TYPE_REFUND = "REFUND"

    def __init__(self, transaction_id: str, user_id: str,
                 transaction_type: str, amount: float,
                 description: str, timestamp: str):
        """
        Initialise a Transaction instance.

        Args:
            transaction_id (str): Unique identifier for this transaction.
            user_id (str): ID of the user this transaction belongs to.
            transaction_type (str): One of TYPE_CREDIT, TYPE_DEBIT, or TYPE_REFUND.
            amount (float): Monetary amount involved in the transaction.
            description (str): Human-readable description of the transaction.
            timestamp (str): Date and time the transaction occurred in dd/mm/yyyy HH:MM format.

        Returns:
            None
        """
        self.__transaction_id = transaction_id
        self.__user_id = user_id
        self.__transaction_type = transaction_type
        self.__amount = float(amount)
        self.__description = description
        self.__timestamp = timestamp

    # --- Getters ---
    def get_transaction_id(self): return self.__transaction_id
    def get_user_id(self): return self.__user_id
    def get_transaction_type(self): return self.__transaction_type
    def get_amount(self): return self.__amount
    def get_description(self): return self.__description
    def get_timestamp(self): return self.__timestamp

    def to_csv_row(self) -> list:
        """
        Serialise the transaction to a flat list suitable for writing as a CSV row.

        Returns:
            list: Ordered list of string values matching the CSV column layout:
                  [transaction_id, user_id, transaction_type, amount, description, timestamp]
        """
        return [
            self.__transaction_id, self.__user_id,
            self.__transaction_type, str(self.__amount),
            self.__description, self.__timestamp
        ]

    def __str__(self):
        """
        Return a human-readable summary of the transaction.

        Returns:
            str: Formatted string showing transaction type, amount, description, and timestamp.
        """
        return (f"[{self.__transaction_type}] ${self.__amount:.2f} | "
                f"{self.__description} | {self.__timestamp}")