"""
Controller class responsible for managing deal packages.
"""

import csv
import os
from datetime import datetime

from entity.deal_package import DealPackage


class DealPackageManager:
    """Manages deal packages from CSV storage."""

    DEALS_FILE = os.path.join(os.path.dirname(__file__), "../data/deals.csv")

    HEADERS = [
        "deal_id", "name", "description", "price",
        "bookable_hours", "applicable_room_type", "valid_until"
    ]

    def __init__(self):
        self.__deals: list[DealPackage] = []
        self.__load_deals()

    def __load_deals(self):
        """Load deals from CSV."""
        self.__deals = []
        path = os.path.abspath(self.DEALS_FILE)
        if not os.path.exists(path):
            return
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                deal = DealPackage(
                    deal_id=row["deal_id"],
                    name=row["name"],
                    description=row["description"],
                    price=float(row["price"]),
                    bookable_hours=float(row["bookable_hours"]),
                    applicable_room_type=row["applicable_room_type"],
                    valid_until=row["valid_until"]
                )
                self.__deals.append(deal)

    def get_available_deals(self) -> list[DealPackage]:
        """Return deals that have not expired."""
        today = datetime.today().date()
        available = []
        for d in self.__deals:
            try:
                expiry = datetime.strptime(d.get_valid_until(), "%d/%m/%Y").date()
                if expiry >= today:
                    available.append(d)
            except ValueError:
                available.append(d)
        return available

    def find_deal_by_id(self, deal_id: str) -> DealPackage | None:
        """Find a deal by ID."""
        for d in self.__deals:
            if d.get_deal_id().upper() == deal_id.upper():
                return d
        return None

    def is_deal_eligible(self, deal: DealPackage, room_type: str) -> tuple[bool, str]:
        """
        Check if a deal package is eligible for the given room type.
        Returns (eligible, reason).
        """
        applicable = deal.get_applicable_room_type()
        if applicable.lower() != "any" and applicable.lower() != room_type.lower():
            return False, (f"This deal is only applicable for "
                           f"{applicable} room bookings.")
        return True, ""