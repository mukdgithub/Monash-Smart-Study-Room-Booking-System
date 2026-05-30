"""
Entity class representing a user's purchased instance of a DealPackage.
"""


class UserDeal:
    """
    Represents a single purchased deal instance owned by a student.
    A user may hold multiple UserDeal instances, even from the same DealPackage.
    """

    def __init__(self, deal_instance_id: str, user_id: str,
                 deal_package_id: str, hours_remaining: float,
                 purchased_at: str):
        """
        Initialise a UserDeal instance.

        Args:
            deal_instance_id (str): Unique identifier for this purchased deal instance.
            user_id (str): ID of the student who owns this deal.
            deal_package_id (str): ID of the DealPackage this instance was created from.
            hours_remaining (float): Remaining booking hours available on this deal.
            purchased_at (str): Purchase timestamp in dd/mm/yyyy HH:MM format.

        Returns:
            None
        """
        self.__deal_instance_id = deal_instance_id
        self.__user_id          = user_id
        self.__deal_package_id  = deal_package_id
        self.__hours_remaining  = float(hours_remaining)
        self.__purchased_at     = purchased_at  # dd/mm/yyyy HH:MM

    # --- Getters ---
    def get_deal_instance_id(self) -> str:   return self.__deal_instance_id
    def get_user_id(self) -> str:            return self.__user_id
    def get_deal_package_id(self) -> str:    return self.__deal_package_id
    def get_hours_remaining(self) -> float:  return self.__hours_remaining
    def get_purchased_at(self) -> str:       return self.__purchased_at

    # --- Setters ---
    def set_hours_remaining(self, val: float):
        self.__hours_remaining = float(val)

    def is_exhausted(self) -> bool:
        """
        Check whether this deal instance has no booking hours remaining.

        Returns:
            bool: True if hours_remaining is zero or below.
        """
        return self.__hours_remaining <= 0.0

    def to_csv_row(self) -> list:
        """
        Serialise the user deal to a flat list suitable for writing as a CSV row.

        Returns:
            list: Ordered list of string values matching the CSV column layout:
                  [deal_instance_id, user_id, deal_package_id, hours_remaining, purchased_at]
        """
        return [
            self.__deal_instance_id, self.__user_id,
            self.__deal_package_id, str(self.__hours_remaining),
            self.__purchased_at
        ]

    def __str__(self):
        """
        Return a human-readable summary of the user deal instance.

        Returns:
            str: Formatted string showing instance ID, package ID, hours remaining, and purchase date.
        """
        return (f"[{self.__deal_instance_id}] Package: {self.__deal_package_id} | "
                f"{self.__hours_remaining:.1f} hrs remaining | "
                f"Purchased: {self.__purchased_at}")