"""
Controller class responsible for managing user-owned Deal instances.
"""

import csv
import os
import uuid
from datetime import datetime

from entity.user_deal import UserDeal
from entity.deal_package import DealPackage


class UserDealManager:
    """
    Manages Deal instances — the purchased deals owned by users.
    Distinct from DealPackageManager which manages the DealPackage catalogue.
    """

    DEALS_OWNED_FILE = os.path.join(os.path.dirname(__file__), "../data/deals_owned.csv")

    HEADERS = [
        "deal_instance_id", "user_id", "deal_package_id",
        "hours_remaining", "purchased_at"
    ]

    def __init__(self):
        self.__deals: list[UserDeal] = []
        self.__load_deals()

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def __load_deals(self):
        self.__deals = []
        path = os.path.abspath(self.DEALS_OWNED_FILE)
        if not os.path.exists(path):
            return
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.__deals.append(UserDeal(
                    deal_instance_id=row["deal_instance_id"],
                    user_id=row["user_id"],
                    deal_package_id=row["deal_package_id"],
                    hours_remaining=float(row["hours_remaining"]),
                    purchased_at=row["purchased_at"]
                ))

    def __save_deals(self):
        path = os.path.abspath(self.DEALS_OWNED_FILE)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADERS)
            for d in self.__deals:
                writer.writerow(d.to_csv_row())

    def __generate_instance_id(self) -> str:
        return "DI" + str(uuid.uuid4())[:8].upper()

    # ------------------------------------------------------------------ #
    #  Public methods                                                        #
    # ------------------------------------------------------------------ #

    def create_deal_instance(self, user_id: str,
                              deal_package: DealPackage) -> UserDeal:
        """
        Create and persist a new Deal instance after a successful purchase.
        Returns the new Deal.
        """
        instance = UserDeal(
            deal_instance_id=self.__generate_instance_id(),
            user_id=user_id,
            deal_package_id=deal_package.get_deal_id(),
            hours_remaining=deal_package.get_bookable_hours(),
            purchased_at=datetime.now().strftime("%d/%m/%Y %H:%M")
        )
        self.__deals.append(instance)
        self.__save_deals()
        return instance

    def get_deals_for_user(self, user_id: str) -> list[UserDeal]:
        """Return all deal instances owned by a user, including exhausted ones."""
        return [d for d in self.__deals if d.get_user_id() == user_id]

    def get_active_deals_for_user(self, user_id: str) -> list[UserDeal]:
        """Return only deal instances with hours remaining."""
        return [
            d for d in self.__deals
            if d.get_user_id() == user_id and not d.is_exhausted()
        ]

    def find_instance_by_id(self, deal_instance_id: str) -> UserDeal | None:
        """Find a deal instance by its instance ID."""
        for d in self.__deals:
            if d.get_deal_instance_id() == deal_instance_id:
                return d
        return None

    def get_eligible_deals_for_booking(self, user_id: str,
                                        room_type: str,
                                        deal_package_manager) -> list[UserDeal]:
        """
        Return active deals owned by the user that are eligible
        for the given room type, resolved against the package catalogue.
        """
        eligible = []
        for deal in self.get_active_deals_for_user(user_id):
            package = deal_package_manager.find_deal_by_id(
                deal.get_deal_package_id()
            )
            if not package:
                continue
            applicable = package.get_applicable_room_type()
            if applicable.lower() == "any" or applicable.lower() == room_type.lower():
                eligible.append(deal)
        return eligible

    def consume_hours(self, deal: UserDeal, hours: float) -> bool:
        """
        Deduct hours from a deal instance and persist.
        Returns False if insufficient hours.
        """
        if deal.get_hours_remaining() < hours:
            return False
        deal.set_hours_remaining(deal.get_hours_remaining() - hours)
        self.__save_deals()
        return True

    def restore_hours(self, deal: UserDeal, hours: float):
        """Restore hours to a deal instance (used on refund/rollback)."""
        deal.set_hours_remaining(deal.get_hours_remaining() + hours)
        print(f" Restored hours: {hours}")
        print(f" Remaining hours: {deal.get_hours_remaining()}")
        self.__save_deals()

    def save_deal(self, deal: UserDeal):
        """Persist a single deal instance's updated state."""
        for d in self.__deals:
            if d.get_deal_instance_id() == deal.get_deal_instance_id():
                d.set_hours_remaining(deal.get_hours_remaining())
        self.__save_deals()