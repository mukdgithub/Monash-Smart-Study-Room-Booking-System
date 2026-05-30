"""
Controller class responsible for room management and filtering.

Design notes:
  - standard_equipment on a Room instance is a human-readable summary string
    derived from StandardEquipmentManager at load time (e.g. "1 x Table, 2 x Chair").
  - The ground truth for individual equipment units lives in standard_equipment.csv
    and is managed by StandardEquipmentManager.
  - rooms.csv keeps a standard_equipment summary column purely for readability;
    it is always regenerated from StandardEquipmentManager on load and overwritten
    on save, so it is never the authoritative source.
"""

import csv
import os

from entity.room import Room
from controller.standard_equipment_manager import StandardEquipmentManager


class RoomManager:
    """Manages room data including creation, updates, deletion, and filtering."""

    ROOMS_FILE = os.path.join(os.path.dirname(__file__), "../data/rooms.csv")
    PRICES_FILE = os.path.join(os.path.dirname(__file__), "../data/prices.csv")

    HEADERS = [
        "room_id", "room_type", "location", "standard_equipment",
        "price_per_hour", "is_available", "opening_time", "closing_time"
    ]

    PRICES = {}

    @classmethod
    def load_room_prices(cls):
        """
        Load room prices from prices.csv into the class-level PRICES dict.

        Returns:
            None
        """
        with open(os.path.abspath(cls.PRICES_FILE), "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cls.PRICES[row["room_type"]] = float(row["price_per_hour"])

    @classmethod
    def save_room_prices(cls):
        """
        Persist the current PRICES dict back to prices.csv, then reload it.

        Returns:
            None
        """
        with open(os.path.abspath(cls.PRICES_FILE), "w", encoding="utf-8") as f:
            f.write("room_type,price_per_hour\n")
            for r in cls.PRICES.keys():
                f.write(f"{r},{cls.PRICES[r]}\n")
        RoomManager.load_room_prices()

    def __init__(self):
        """
        Initialise RoomManager, load equipment data, rooms, and room prices from CSV.

        Returns:
            None
        """
        self.__rooms: list[Room] = []
        self.__se_manager = StandardEquipmentManager()
        self.__load_rooms()
        RoomManager.load_room_prices()

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def get_se_manager(self) -> StandardEquipmentManager:
        """Return the StandardEquipmentManager instance used by this RoomManager."""
        return self.__se_manager

    def __load_rooms(self):
        """Load rooms from CSV into memory.

        The standard_equipment summary on each Room is derived from
        StandardEquipmentManager — the rooms.csv column is ignored on read
        and always regenerated from standard_equipment.csv.
        """
        self.__rooms = []
        path = os.path.abspath(self.ROOMS_FILE)
        if not os.path.exists(path):
            return
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Overrides the stale summary column in rooms.csv with live data from standard_equipment.csv
                equipment_summary = self.__se_manager.get_equipment_summary_by_room(
                    row["room_id"]
                )
                room = Room(
                    room_id=row["room_id"],
                    room_type=row["room_type"],
                    location=row["location"],
                    standard_equipment=equipment_summary,
                    price_per_hour=float(row["price_per_hour"]),
                    is_available=row.get("is_available", "True") == "True",  # CSV stores booleans as strings
                    opening_time=row.get("opening_time", "08:00"),
                    closing_time=row.get("closing_time", "22:00")
                )
                self.__rooms.append(room)

    def __save_rooms(self):
        """Persist all rooms back to CSV."""
        path = os.path.abspath(self.ROOMS_FILE)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADERS)
            for r in self.__rooms:
                writer.writerow(r.to_csv_row())
        self.__load_rooms()


    def __generate_room_id(self) -> str:
        """
        Generate the next sequential room ID not already in use.

        Returns:
            str: A room ID in the format 'R001', 'R002', etc.
        """
        existing = {r.get_room_id() for r in self.__rooms}
        i = 1
        while True:
            rid = f"R{i:03d}"
            if rid not in existing:
                return rid
            i += 1

    # ------------------------------------------------------------------ #
    #  Public methods                                                        #
    # ------------------------------------------------------------------ #

    def get_all_rooms(self) -> list[Room]:
        """Return all rooms."""
        return list(self.__rooms)

    def get_available_rooms(self) -> list[Room]:
        """Return only available rooms."""
        return [r for r in self.__rooms if r.get_is_available()]

    def find_room_by_id(self, room_id: str) -> Room | None:
        """Find a room by its ID."""
        for r in self.__rooms:
            if r.get_room_id().upper() == room_id.upper():
                return r
        return None

    def view_room_by_filtering(self, rooms: list[Room] = None,
                               max_price: float = None,
                               min_capacity: int = None,
                               room_type: str = None,
                               location_keyword: str = None,
                               equipment_keyword: str = None) -> list[Room]:
        """
        Filter rooms by various criteria. All filters are optional and cumulative.
        Filter logic lives here, not in boundary classes.
        """
        results = rooms if rooms is not None else self.get_available_rooms()

        if max_price is not None:
            results = [r for r in results if r.get_price_per_hour() <= max_price]

        if min_capacity is not None:
            def meets_capacity(room: Room) -> bool:
                cap_str = room.get_capacity_str()   # e.g. "1-2" or "3-6"
                try:
                    upper = int(cap_str.split("-")[1])
                    return upper >= min_capacity
                except Exception:
                    return False
            results = [r for r in results if meets_capacity(r)]

        if room_type is not None:
            results = [r for r in results if r.get_room_type().lower() == room_type.lower()]

        if location_keyword is not None:
            kw = location_keyword.lower()
            results = [r for r in results if kw in r.get_location().lower()]

        if equipment_keyword is not None:
            kw = equipment_keyword.lower()
            results = self.__se_manager.search_rooms_by_keyword(kw, results)  # delegates to StandardEquipmentManager, passing the already-filtered room list

        return results

    def add_room(self, room_type: str, location: str) -> tuple[bool, str]:
        """Add a new room. Returns (success, room_id or error message).

        Standard equipment units should be registered separately via
        StandardEquipmentManager.add_equipment() or add_equipment_bulk()
        after the room is created. The equipment summary on the Room instance
        is then refreshed via refresh_room_equipment().
        """
        if room_type.lower() not in Room.VALID_TYPES:
            return False, f"Invalid room type. Must be one of: {', '.join(Room.VALID_TYPES)}."
        if not location.strip():
            return False, "Location cannot be empty."
        room_id = self.__generate_room_id()
        price = RoomManager.PRICES[room_type.lower()]  # class-level dict populated from prices.csv
        new_room = Room(room_id, room_type.lower(), location.strip(), "None", price)
        self.__rooms.append(new_room)
        self.__save_rooms()
        return True, room_id

    def refresh_room_equipment(self, room_id: str):
        """Refresh the standard_equipment summary on a Room instance from
        StandardEquipmentManager. Call this after adding/updating/deleting
        equipment units for a room."""
        room = self.find_room_by_id(room_id)
        if room:
            summary = self.__se_manager.get_equipment_summary_by_room(room_id)
            room.set_standard_equipment(summary)
            self.__save_rooms()

    def update_room(self, room_id: str, location: str = None,
                    opening_time: str = None,
                    closing_time: str = None) -> tuple[bool, str]:
        """Update room details. Returns (success, message).
        To update standard equipment units, use StandardEquipmentManager directly,
        then call refresh_room_equipment(room_id) to sync the summary."""
        from datetime import datetime

        room = self.find_room_by_id(room_id)
        if not room:
            return False, f"Room {room_id} not found."

        parsed_open = None
        parsed_close = None
        if opening_time is not None:
            try:
                parsed_open = datetime.strptime(opening_time.strip(), "%H:%M").time()
            except ValueError:
                return False, f"Invalid opening time '{opening_time}'. Expected HH:MM format (e.g. 08:00)."
        if closing_time is not None:
            try:
                parsed_close = datetime.strptime(closing_time.strip(), "%H:%M").time()
            except ValueError:
                return False, f"Invalid closing time '{closing_time}'. Expected HH:MM format (e.g. 22:00)."

        final_open = parsed_open if parsed_open else datetime.strptime(room.get_opening_time(), "%H:%M").time()    # falls back to the room's existing time if no new value was provided
        final_close = parsed_close if parsed_close else datetime.strptime(room.get_closing_time(), "%H:%M").time()  # same fallback for closing time
        if final_close <= final_open:
            return False, "Closing time must be after opening time."

        if location is not None:
            room.set_location(location.strip())
        if opening_time is not None:
            room.set_opening_time(opening_time.strip())
        if closing_time is not None:
            room.set_closing_time(closing_time.strip())
        self.__save_rooms()
        return True, f"Room {room_id} updated successfully."

    def delete_room(self, room_id: str) -> tuple[bool, str]:
        """Delete a room by ID. All standard equipment assigned to the room
        is moved to inventory rather than permanently deleted."""
        room = self.find_room_by_id(room_id)
        if not room:
            return False, f"Room {room_id} not found."
        self.__se_manager.unassign_all_from_room(room_id)  # moves all assigned equipment back to inventory before removing the room
        self.__rooms.remove(room)
        self.__save_rooms()
        return True, f"Room {room_id} has been deleted."

    def set_room_availability(self, room_id: str, available: bool) -> tuple[bool, str]:
        """Suspend or restore a room."""
        room = self.find_room_by_id(room_id)
        if not room:
            return False, f"Room {room_id} not found."
        room.set_is_available(available)
        self.__save_rooms()
        status = "available" if available else "suspended"
        return True, f"Room {room_id} is now {status}."

    def update_room_price(self, room_type: str, new_price: float) -> tuple[bool, str]:
        """Update price for a room type and persist to CSV."""
        if room_type not in Room.VALID_TYPES:
            return False, f"Invalid room type."
        if new_price <= 0:
            return False, "Price must be greater than zero."
        # Only update AFTER this method is called (i.e. after user confirms)
        RoomManager.PRICES[room_type] = new_price
        for room in self.__rooms:
            if room.get_room_type() == room_type:
                room.set_price_per_hour(new_price)
        self.__save_rooms()
        return True, f"Price for {room_type.capitalize()} rooms updated to ${new_price:.2f}/hr."