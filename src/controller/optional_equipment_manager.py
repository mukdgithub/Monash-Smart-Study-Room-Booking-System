"""
Controller class responsible for managing optional equipment.

Design notes:
  - Each CSV row represents ONE physical unit of equipment.
  - Availability is determined dynamically by checking active bookings,
    not by a stored field. A unit is available if it is not already
    assigned to an active booking that overlaps the requested time slot.
  - No price is stored on equipment. A flat $100 deposit applies per
    booking if any equipment is selected (handled by BookingManager).
"""

import csv
import os

from entity.optional_equipment import OptionalEquipment


class OptionalEquipmentManager:
    """Manages optional equipment CRUD and availability checking."""

    EQUIPMENT_FILE = os.path.join(os.path.dirname(__file__),
                                   "../data/optional_equipment.csv")

    HEADERS = ["equipment_id", "name", "description"]

    def __init__(self):
        self.__equipment: list[OptionalEquipment] = []
        self.__load_equipment()

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def __load_equipment(self):
        """Load all equipment units from CSV into memory."""
        self.__equipment = []
        path = os.path.abspath(self.EQUIPMENT_FILE)
        if not os.path.exists(path):
            return
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                item = OptionalEquipment(
                    equipment_id=row["equipment_id"],
                    name=row["name"],
                    description=row["description"]
                )
                self.__equipment.append(item)

    def __save_equipment(self):
        """Persist all equipment units back to CSV."""
        path = os.path.abspath(self.EQUIPMENT_FILE)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADERS)
            for item in self.__equipment:
                writer.writerow(item.to_csv_row())

    def __generate_equipment_id(self) -> str:
        """Generate the next sequential unique equipment ID (e.g. OE011)."""
        existing = {e.get_equipment_id() for e in self.__equipment}
        i = 1
        while True:
            eid = f"OE{i:03d}"
            if eid not in existing:
                return eid
            i += 1

    # ------------------------------------------------------------------ #
    #  Public methods — Read                                                #
    # ------------------------------------------------------------------ #

    def get_all_equipment(self) -> list[OptionalEquipment]:
        """Return all equipment units registered in the system."""
        return list(self.__equipment)

    def find_equipment_by_id(self, equipment_id: str) -> OptionalEquipment | None:
        """Find a specific equipment unit by its unique ID (case-insensitive)."""
        for e in self.__equipment:
            if e.get_equipment_id().upper() == equipment_id.upper():
                return e
        return None

    def find_equipment_by_ids(self, ids: list[str]) -> list[OptionalEquipment]:
        """Return equipment units matching the given list of IDs."""
        result = []
        for eid in ids:
            item = self.find_equipment_by_id(eid)
            if item:
                result.append(item)
        return result

    def get_available_equipment_for_slot(self, time_slot,
                                          bookings: list) -> list[OptionalEquipment]:
        """
        Return equipment units that are NOT already rented in any active booking
        that overlaps with the given time slot.

        A unit is considered rented if its equipment_id appears in any active
        booking whose time slot overlaps with the requested slot.

        Args:
            time_slot: the TimeSlot the student wants to book
            bookings:  all bookings in the system (from BookingManager)
        """
        from entity.booking import Booking

        # Collect IDs of units already rented during this time slot
        rented_ids = set()
        for booking in bookings:
            if booking.get_status() not in (
                Booking.STATUS_ACTIVE, "CHECK_IN_REQUESTED", "CHECKED_IN"
            ):
                continue
            if time_slot.overlaps_with(booking.get_time_slot()):
                for item in booking.get_optional_equipment():
                    rented_ids.add(item.get_equipment_id())

        # Return units not in the rented set
        return [e for e in self.__equipment
                if e.get_equipment_id() not in rented_ids]

    # ------------------------------------------------------------------ #
    #  Public methods — Create                                              #
    # ------------------------------------------------------------------ #

    def add_equipment(self, name: str,
                      description: str) -> tuple[bool, str]:
        """
        Register a new physical equipment unit.
        Returns (success, equipment_id or error message).
        """
        if not name.strip():
            return False, "Equipment name cannot be empty."

        equipment_id = self.__generate_equipment_id()
        new_item = OptionalEquipment(
            equipment_id=equipment_id,
            name=name.strip(),
            description=description.strip()
        )
        self.__equipment.append(new_item)
        self.__save_equipment()
        return True, equipment_id

    # ------------------------------------------------------------------ #
    #  Public methods — Update                                              #
    # ------------------------------------------------------------------ #

    def update_equipment(self, equipment_id: str,
                         name: str = None,
                         description: str = None) -> tuple[bool, str]:
        """
        Update an equipment unit's name or description.
        Only non-None fields are updated.
        Returns (success, message).
        """
        item = self.find_equipment_by_id(equipment_id)
        if not item:
            return False, f"Equipment ID {equipment_id} not found."

        if name is not None:
            if not name.strip():
                return False, "Equipment name cannot be empty."
            item.set_name(name.strip())

        if description is not None:
            item.set_description(description.strip())

        self.__save_equipment()
        return True, f"Equipment {equipment_id} updated successfully."

    # ------------------------------------------------------------------ #
    #  Public methods — Delete                                              #
    # ------------------------------------------------------------------ #

    def delete_equipment(self, equipment_id: str) -> tuple[bool, str]:
        """
        Remove an equipment unit from the system by ID.
        Returns (success, message).
        """
        item = self.find_equipment_by_id(equipment_id)
        if not item:
            return False, f"Equipment ID {equipment_id} not found."
        self.__equipment.remove(item)
        self.__save_equipment()
        return True, (f"Equipment '{item.get_name()}' "
                      f"({equipment_id}) has been deleted.")