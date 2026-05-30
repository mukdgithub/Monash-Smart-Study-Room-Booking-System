"""
Entity class representing an optional equipment in MSSRB system.

Design rules:
    - Each instance represents one physical unit (e.g. one specific laptop)
    - There is no per-unit price. A flat $100 deposit is charged per booking.
"""

class OptionalEquipment:
    """Represents a single physical unit of optional equipment in MSSRB system."""

    def __init__(self, equipment_id: str, name: str, description: str):
        """Initializes a optional equipment in MSSRB system.

            Args:
                equipment_id (str): The equipment ID.
                name (str): The name of the equipment.
                description (str): The description of the equipment.
        """
        self.__equipment_id = equipment_id
        self.__name = name
        self.__description = description

    # -------------------------------------------------------------- #
    # Getters
    # -------------------------------------------------------------- #

    def get_equipment_id(self) -> str: return self.__equipment_id
    def get_name(self) -> str: return self.__name
    def get_description(self) -> str: return self.__description

    # -------------------------------------------------------------- #
    # Setters
    # -------------------------------------------------------------- #

    def set_name(self, val: str): self.__name = val.strip()
    def set_description(self, val: str): self.__description = val.strip()

    # -------------------------------------------------------------- #
    # Serialisation
    # -------------------------------------------------------------- #

    def to_csv_row(self) -> list:
        return [self.__equipment_id,self.__name, self.__description]

    def __str__(self) -> str:
        return f"[{self.__equipment_id}] {self.__name} | {self.__description}"