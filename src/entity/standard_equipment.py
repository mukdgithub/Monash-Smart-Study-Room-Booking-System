"""
Entity class representing a physical unit of standard equipment in the MSSRB system.

Design rules:
    - Standard equipment is a movable asset that is either installed in a specific
      room (room_id set) or held in inventory (room_id is None).
    - Each instance represents ONE physical unit.
    - Status tracks the condition of the unit: available, under_maintenance,
      or damaged. Units in inventory retain their status.
    - There is no deposit or price for standard equipment.
"""


class StandardEquipment:
    """Represents a single physical unit of standard (built-in) room equipment."""

    STATUS_AVAILABLE         = "available"
    STATUS_UNDER_MAINTENANCE = "under_maintenance"
    STATUS_DAMAGED           = "damaged"

    VALID_STATUSES = [STATUS_AVAILABLE, STATUS_UNDER_MAINTENANCE, STATUS_DAMAGED]

    def __init__(self, equipment_id: str, room_id: str | None,
                 name: str, status: str = STATUS_AVAILABLE):
        """Initialise a standard equipment unit.

        Args:
            equipment_id (str): Unique identifier, e.g. 'SE001'.
            room_id      (str | None): The room this unit is installed in, e.g. 'R001'.
                                       None means the unit is held in inventory.
            name         (str): Equipment type name, e.g. 'Chair', 'Projector'.
            status       (str): Current condition. Defaults to 'available'.
        """
        self.__equipment_id = equipment_id
        self.__room_id      = room_id
        self.__name         = name.strip()
        self.__status       = status.strip().lower()

    # -------------------------------------------------------------- #
    # Getters
    # -------------------------------------------------------------- #

    def get_equipment_id(self) -> str: return self.__equipment_id
    def get_room_id(self)      -> str | None: return self.__room_id
    def get_name(self)         -> str: return self.__name
    def get_status(self)       -> str: return self.__status

    def is_available(self) -> bool:
        return self.__status == self.STATUS_AVAILABLE

    def is_in_inventory(self) -> bool:
        """Return True if this unit is not assigned to any room."""
        return self.__room_id is None

    # -------------------------------------------------------------- #
    # Setters
    # -------------------------------------------------------------- #

    def set_room_id(self, val: str | None):
        """Assign to a room (str) or move to inventory (None)."""
        self.__room_id = val

    def set_name(self, val: str):
        self.__name = val.strip()

    def set_status(self, val: str):
        val = val.strip().lower()
        if val not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{val}'. "
                f"Must be one of: {', '.join(self.VALID_STATUSES)}."
            )
        self.__status = val

    # -------------------------------------------------------------- #
    # Serialisation
    # -------------------------------------------------------------- #

    def to_csv_row(self) -> list:
        return [self.__equipment_id, self.__room_id if self.__room_id else "",
                self.__name, self.__status]

    def __str__(self) -> str:
        location = f"Room: {self.__room_id}" if self.__room_id else "Inventory"
        return (f"[{self.__equipment_id}] {self.__name} "
                f"| {location} | Status: {self.__status}")