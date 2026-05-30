"""
Entity class representing a deal package in the MSSRB system.
"""


class DealPackage:
    """Represents a purchasable deal package."""

    def __init__(self, deal_id: str, name: str, description: str,
                 price: float, bookable_hours: float,
                 applicable_room_type: str, valid_until: str):
        self.__deal_id = deal_id
        self.__name = name
        self.__description = description
        self.__price = float(price)
        self.__bookable_hours = float(bookable_hours)
        self.__applicable_room_type = applicable_room_type  # "small", "any", etc.
        self.__valid_until = valid_until  # dd/mm/yyyy

    # --- Getters ---
    def get_deal_id(self): return self.__deal_id
    def get_name(self): return self.__name
    def get_description(self): return self.__description
    def get_price(self): return self.__price
    def get_bookable_hours(self): return self.__bookable_hours
    def get_applicable_room_type(self): return self.__applicable_room_type
    def get_valid_until(self): return self.__valid_until

    def to_csv_row(self) -> list:
        return [
            self.__deal_id, self.__name, self.__description,
            str(self.__price), str(self.__bookable_hours),
            self.__applicable_room_type, self.__valid_until
        ]

    def __str__(self):
        return (f"[{self.__deal_id}] {self.__name} | "
                f"{self.__bookable_hours} hrs | ${self.__price} | "
                f"Room: {self.__applicable_room_type} | Until: {self.__valid_until}")