"""
Repository class responsible for loading and persisting Booking data.

All CSV I/O for bookings lives here.  No business logic of any kind.
"""

import csv
import os
import uuid

from entity.booking import Booking
from entity.time_slot import TimeSlot
from controller.optional_equipment_manager import OptionalEquipmentManager


class BookingRepository:
    """
    Handles all CSV persistence for Booking objects.

    Responsibilities:
      - Load bookings from bookings.csv on construction
      - Save (overwrite) bookings.csv when asked
      - Provide raw list access and id-based lookup
      - Generate new booking IDs

    Intentionally knows nothing about fees, refunds, check-in rules,
    validation, or any other business concern.
    """

    BOOKINGS_FILE = os.path.join(os.path.dirname(__file__), "../data/bookings.csv")

    HEADERS = [
        "booking_id", "user_id", "room_id", "date", "start_time",
        "end_time", "duration_hours", "optional_equipment",
        "total_fee", "status", "deal_instance_id", "created_at", "checked_in_at"
    ]

    def __init__(self, oe_manager: OptionalEquipmentManager):
        self.__oe_manager = oe_manager
        self.__bookings: list[Booking] = []
        self.__load()

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def __load(self):
        """Load all bookings from CSV into memory."""
        self.__bookings = []
        path = os.path.abspath(self.BOOKINGS_FILE)
        if not os.path.exists(path):
            return
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    time_slot = TimeSlot.from_csv(
                        row["date"], row["start_time"], row["end_time"]
                    )
                except ValueError:
                    continue  # skip malformed rows

                oe_ids_str = row.get("optional_equipment", "")
                oe_ids     = [eid.strip() for eid in oe_ids_str.split(",") if eid.strip()]
                oe_objects = self.__oe_manager.find_equipment_by_ids(oe_ids)

                b = Booking(
                    booking_id=row["booking_id"],
                    user_id=row["user_id"],
                    room_id=row["room_id"],
                    time_slot=time_slot,
                    optional_equipment=oe_objects,
                    total_fee=float(row["total_fee"]),
                    status=row["status"],
                    deal_instance_id=row.get("deal_instance_id", ""),
                    created_at=row.get("created_at", ""),
                    checked_in_at=row.get("checked_in_at", "")
                )
                self.__bookings.append(b)

    # ------------------------------------------------------------------ #
    #  Public interface                                                     #
    # ------------------------------------------------------------------ #

    def save(self):
        """Persist all in-memory bookings to CSV (full overwrite)."""
        path = os.path.abspath(self.BOOKINGS_FILE)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADERS)
            for b in self.__bookings:
                writer.writerow(b.to_csv_row())

    def add(self, booking: Booking):
        """Append a new booking to the in-memory list and persist immediately."""
        self.__bookings.append(booking)
        self.save()

    def get_all(self) -> list[Booking]:
        """Return a shallow copy of all bookings."""
        return list(self.__bookings)

    def find_by_id(self, booking_id: str) -> Booking | None:
        """Return the booking with the given ID, or None."""
        for b in self.__bookings:
            if b.get_booking_id() == booking_id:
                return b
        return None

    def generate_id(self) -> str:
        """Return a new unique booking ID."""
        return "B" + str(uuid.uuid4())[:8].upper()