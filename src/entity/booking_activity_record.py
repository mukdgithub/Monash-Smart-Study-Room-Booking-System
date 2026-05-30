"""
Entity class representing a read-only activity record derived from a Booking.

Used by BookingManager.get_activity_records() to return a chronologically
sortable, display-friendly view of a user's booking history.
"""

from entity.booking import Booking


class BookingActivityRecord:
    """
    A lightweight, read-only summary of a single booking event.

    Attributes:
        booking_id  -- original booking ID
        room_id     -- room that was booked
        date        -- booking date as dd/mm/yyyy
        time        -- booking start time as HH:MM (used as the sort key)
        end_time    -- booking end time as HH:MM
        status      -- final booking status (ACTIVE, CANCELLED, COMPLETED, etc.)
        total_fee   -- amount charged for the booking
    """

    def __init__(self, booking_id: str, room_id: str,
                 date: str, time: str, end_time: str,
                 status: str, total_fee: float):
        self.__booking_id = booking_id
        self.__room_id    = room_id
        self.__date       = date        # dd/mm/yyyy — used for chronological sort
        self.__time       = time        # HH:MM start time — used for chronological sort
        self.__end_time   = end_time
        self.__status     = status
        self.__total_fee  = float(total_fee)

    # ------------------------------------------------------------------ #
    #  Getters                                                              #
    # ------------------------------------------------------------------ #

    def get_booking_id(self) -> str:  return self.__booking_id
    def get_room_id(self) -> str:     return self.__room_id
    def get_date(self) -> str:        return self.__date
    def get_time(self) -> str:        return self.__time
    def get_end_time(self) -> str:    return self.__end_time
    def get_status(self) -> str:      return self.__status
    def get_total_fee(self) -> float: return self.__total_fee

    # ------------------------------------------------------------------ #
    #  Factory                                                              #
    # ------------------------------------------------------------------ #

    @classmethod
    def from_booking(cls, booking: Booking) -> "BookingActivityRecord":
        """
        Construct a BookingActivityRecord from a Booking entity.
        This is the only intended way to create instances of this class.
        """
        return cls(
            booking_id=booking.get_booking_id(),
            room_id=booking.get_room_id(),
            date=booking.get_date(),
            time=booking.get_start_time(),
            end_time=booking.get_end_time(),
            status=booking.get_status(),
            total_fee=booking.get_total_fee(),
        )

    # ------------------------------------------------------------------ #
    #  Display                                                              #
    # ------------------------------------------------------------------ #

    def __str__(self) -> str:
        return (f"[{self.__booking_id}] Room {self.__room_id} | "
                f"{self.__date} {self.__time}–{self.__end_time} | "
                f"{self.__status} | ${self.__total_fee:.2f}")
