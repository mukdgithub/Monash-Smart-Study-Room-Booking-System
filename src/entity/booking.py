"""
Entity class representing a room booking in the MSSRB system.
"""

from entity.time_slot import TimeSlot
from entity.optional_equipment import OptionalEquipment


class Booking:
    """Represents a single room booking made by a student."""

    # ------------------------------------------------------------------ #
    #  Status constants                                                     #
    # ------------------------------------------------------------------ #
    STATUS_ACTIVE               = "ACTIVE"
    STATUS_CHECK_IN_REQUESTED   = "CHECK_IN_REQUESTED"
    STATUS_CHECKED_IN           = "CHECKED_IN"
    STATUS_NO_SHOW              = "NO_SHOW"
    STATUS_CANCELLED            = "CANCELLED"
    STATUS_COMPLETED            = "COMPLETED"

    # Statuses that count as "active/ongoing" for conflict and limit checks
    ACTIVE_STATUSES = {STATUS_ACTIVE, STATUS_CHECK_IN_REQUESTED, STATUS_CHECKED_IN}

    # Flat deposit charged when any optional equipment is selected.
    # Always fully refunded on cancellation regardless of timing or room type.
    EQUIPMENT_DEPOSIT = 100.0

    def __init__(self, booking_id: str, user_id: str, room_id: str,
                 time_slot: TimeSlot,
                 optional_equipment: list,
                 total_fee: float,
                 status: str = "ACTIVE",
                 deal_instance_id: str = "",
                 created_at: str = "",
                 checked_in_at: str = ""):
        """
        Initialise a Booking.

        Args:
            booking_id:         unique booking identifier
            user_id:            ID of the student who made the booking
            room_id:            ID of the booked room
            time_slot:          TimeSlot entity holding date and time range
            optional_equipment: list of OptionalEquipment objects selected
            total_fee:          total charged amount
            status:             ACTIVE | CHECK_IN_REQUESTED | CHECKED_IN |
                                NO_SHOW | CANCELLED | COMPLETED
            deal_instance_id:   UserDeal instance ID used for payment, if any
            created_at:         timestamp of booking creation (dd/mm/yyyy HH:MM)
            checked_in_at:      timestamp of check-in (dd/mm/yyyy HH:MM) or ""
        """
        self.__booking_id       = booking_id
        self.__user_id          = user_id
        self.__room_id          = room_id
        self.__time_slot        = time_slot
        self.__optional_equipment: list[OptionalEquipment] = optional_equipment or []
        self.__total_fee        = float(total_fee)
        self.__status           = status
        self.__deal_instance_id = deal_instance_id   # was: deal_applied (package ID)
        self.__created_at       = created_at
        self.__checked_in_at    = checked_in_at

    # ------------------------------------------------------------------ #
    #  Getters                                                              #
    # ------------------------------------------------------------------ #

    def get_booking_id(self) -> str:            return self.__booking_id
    def get_user_id(self) -> str:               return self.__user_id
    def get_room_id(self) -> str:               return self.__room_id
    def get_time_slot(self) -> TimeSlot:        return self.__time_slot
    def get_date(self) -> str:                  return self.__time_slot.get_date()
    def get_start_time(self) -> str:            return self.__time_slot.get_start_time()
    def get_end_time(self) -> str:              return self.__time_slot.get_end_time()
    def get_duration_hours(self) -> float:      return self.__time_slot.get_duration_hours()
    def get_optional_equipment(self) -> list:   return self.__optional_equipment
    def get_total_fee(self) -> float:           return self.__total_fee
    def get_status(self) -> str:                return self.__status
    def get_deal_instance_id(self) -> str:      return self.__deal_instance_id
    def get_created_at(self) -> str:            return self.__created_at
    def get_checked_in_at(self) -> str:         return self.__checked_in_at

    def get_optional_equipment_names(self) -> str:
        if not self.__optional_equipment:
            return "None"
        return ", ".join(e.get_name() for e in self.__optional_equipment)

    def get_optional_equipment_ids(self) -> str:
        if not self.__optional_equipment:
            return ""
        return ",".join(e.get_equipment_id() for e in self.__optional_equipment)

    def is_active(self) -> bool:
        """Return True if booking is in any active/ongoing state."""
        return self.__status in self.ACTIVE_STATUSES

    def has_equipment(self) -> bool:
        """Return True if any optional equipment was selected for this booking."""
        return len(self.__optional_equipment) > 0

    def was_paid_by_deal(self) -> bool:
        """
        Return True if this booking was paid using a UserDeal instance.
        Relies on deal_instance_id being a non-empty, non-whitespace string.
        """
        return bool(self.__deal_instance_id and self.__deal_instance_id.strip())

    # ------------------------------------------------------------------ #
    #  Setters                                                              #
    # ------------------------------------------------------------------ #

    def set_status(self, val: str):
        self.__status = val

    def set_total_fee(self, val: float):
        self.__total_fee = float(val)

    def set_time_slot(self, time_slot: TimeSlot):
        self.__time_slot = time_slot

    def set_optional_equipment(self, val: list):
        self.__optional_equipment = val or []

    def set_checked_in_at(self, val: str):
        self.__checked_in_at = val

    def set_deal_instance_id(self, val: str):
        self.__deal_instance_id = val

    # ------------------------------------------------------------------ #
    #  Serialisation                                                        #
    # ------------------------------------------------------------------ #

    def to_csv_row(self) -> list:
        date, start, end, duration = self.__time_slot.to_csv_values()
        return [
            self.__booking_id, self.__user_id, self.__room_id,
            date, start, end, str(duration),
            self.get_optional_equipment_ids(),
            str(self.__total_fee), self.__status,
            self.__deal_instance_id, self.__created_at,
            self.__checked_in_at
        ]

    def __str__(self) -> str:
        return (f"Booking {self.__booking_id} | Room {self.__room_id} | "
                f"{self.__time_slot} | "
                f"Equipment: {self.get_optional_equipment_names()} | "
                f"${self.__total_fee:.2f} | {self.__status}")