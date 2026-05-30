"""
Entity class representing a study room in the MSSRB system.
"""


class Room:
    """Represents a bookable study room."""

    VALID_TYPES = ["small", "medium", "large"]
    CAPACITIES  = {"small": "1-2", "medium": "3-6", "large": "5-10"}

    # Maximum allowed units per equipment name for each room type.
    # This is the single source of truth for equipment validation and
    # automatic assignment on room creation.
    STANDARD_EQUIPMENT = {
        "small":  {"Table": 1, "Chair": 2},
        "medium": {"Big Table": 1, "Chair": 6, "Whiteboard": 1},
        "large":  {"Meeting Table": 1, "Chair": 10, "Projector": 1},
    }

    def __init__(self, room_id: str, room_type: str, location: str,
                 standard_equipment: str, price_per_hour: float,
                 is_available: bool = True, opening_time: str = "08:00",
                 closing_time: str = "22:00"):
        """
        Initialise a Room instance.

        Args:
            room_id (str): Unique identifier for the room.
            room_type (str): Room size category — one of 'small', 'medium', or 'large'.
            location (str): Physical location or room number.
            standard_equipment (str): Serialised string describing the room's standard equipment.
            price_per_hour (float): Hourly booking rate.
            is_available (bool): Whether the room is open for booking; defaults to True.
            opening_time (str): Daily opening time in HH:MM format; defaults to '08:00'.
            closing_time (str): Daily closing time in HH:MM format; defaults to '22:00'.

        Returns:
            None
        """
        self.__room_id = room_id
        self.__room_type = room_type.lower()
        self.__location = location
        self.__standard_equipment = standard_equipment
        self.__price_per_hour = float(price_per_hour)
        self.__is_available = is_available
        self.__opening_time = opening_time
        self.__closing_time = closing_time

    # --- Getters ---
    def get_room_id(self): return self.__room_id
    def get_room_type(self): return self.__room_type
    def get_location(self): return self.__location
    def get_standard_equipment(self): return self.__standard_equipment
    def get_price_per_hour(self): return self.__price_per_hour
    def get_is_available(self): return self.__is_available
    def get_opening_time(self): return self.__opening_time
    def get_closing_time(self): return self.__closing_time

    def get_capacity_str(self) -> str:
        return self.CAPACITIES.get(self.__room_type, "N/A")

    # --- Setters ---
    def set_standard_equipment(self, val: str): self.__standard_equipment = val
    def set_is_available(self, val: bool): self.__is_available = val
    def set_opening_time(self, val: str): self.__opening_time = val
    def set_closing_time(self, val: str): self.__closing_time = val
    def set_price_per_hour(self, val: float): self.__price_per_hour = float(val)
    def set_location(self, val: str): self.__location = val

    def to_csv_row(self) -> list:
        """
        Serialise the room to a flat list suitable for writing as a CSV row.

        Returns:
            list: Ordered list of string values matching the CSV column layout:
                  [room_id, room_type, location, standard_equipment,
                   price_per_hour, is_available, opening_time, closing_time]
        """
        return [
            self.__room_id, self.__room_type, self.__location,
            self.__standard_equipment, str(self.__price_per_hour),
            str(self.__is_available), self.__opening_time, self.__closing_time
        ]

    def __str__(self):
        """
        Return a human-readable summary of the room.

        Returns:
            str: Formatted string showing room ID, type, location, capacity,
                 price, availability, equipment, and operating hours.
        """
        avail = "Available" if self.__is_available else "Unavailable"
        return (f"Room {self.__room_id} | {self.__room_type.capitalize()} | "
                f"{self.__location} | Capacity: {self.get_capacity_str()} | "
                f"${self.__price_per_hour}/hr | {avail} | "
                f"{self.__standard_equipment} | "
                f"{self.__opening_time} | {self.__closing_time}")