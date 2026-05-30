"""
Entity class representing a time slot for a room booking.

A TimeSlot encapsulates a booking date, start time, end time,
and derived duration. All time-related data and validation
of the slot itself lives here.
"""

from datetime import datetime


class TimeSlot:
    """
    Represents a specific date and time range for a booking.

    Attributes:
        date        -- booking date as dd/mm/yyyy
        start_time  -- start time as HH:MM
        end_time    -- end time as HH:MM
    """

    DATE_FORMAT = "%d/%m/%Y"
    TIME_FORMAT = "%H:%M"

    def __init__(self, date: str, start_time: str, end_time: str):
        """
        Initialise a TimeSlot.

        Args:
            date:       booking date string in dd/mm/yyyy format
            start_time: start time string in HH:MM format
            end_time:   end time string in HH:MM format

        Raises:
            ValueError: if date or time strings are not in the expected format,
                        or if end_time is not after start_time
        """
        # Validate and parse date
        try:
            self.__date_obj = datetime.strptime(date, self.DATE_FORMAT).date()
        except ValueError:
            raise ValueError(f"Invalid date '{date}'. Expected format: dd/mm/yyyy.")

        # Validate and parse times
        try:
            self.__start_dt = datetime.strptime(start_time, self.TIME_FORMAT)
            self.__end_dt = datetime.strptime(end_time, self.TIME_FORMAT)
        except ValueError:
            raise ValueError(
                f"Invalid time format. Expected HH:MM. "
                f"Got start='{start_time}', end='{end_time}'."
            )

        if self.__end_dt <= self.__start_dt:
            raise ValueError("End time must be after start time.")

        self.__date = date
        self.__start_time = start_time
        self.__end_time = end_time

    # ------------------------------------------------------------------ #
    #  Getters                                                              #
    # ------------------------------------------------------------------ #

    def get_date(self) -> str:
        """Return the booking date as dd/mm/yyyy string."""
        return self.__date

    def get_start_time(self) -> str:
        """Return the start time as HH:MM string."""
        return self.__start_time

    def get_end_time(self) -> str:
        """Return the end time as HH:MM string."""
        return self.__end_time

    def get_date_obj(self):
        """Return the booking date as a Python date object."""
        return self.__date_obj

    def get_start_datetime(self) -> datetime:
        """Return a datetime combining the booking date and start time."""
        return datetime.combine(self.__date_obj, self.__start_dt.time())

    def get_end_datetime(self) -> datetime:
        """Return a datetime combining the booking date and end time."""
        return datetime.combine(self.__date_obj, self.__end_dt.time())

    def get_duration_hours(self) -> float:
        """
        Return the duration of the slot in hours.
        Supports half-hour precision (e.g. 1.5 hours).
        """
        delta = self.__end_dt - self.__start_dt
        return delta.total_seconds() / 3600

    # ------------------------------------------------------------------ #
    #  Utility methods                                                      #
    # ------------------------------------------------------------------ #

    def overlaps_with(self, other: "TimeSlot") -> bool:
        """
        Return True if this time slot overlaps with another on the same date.
        Two slots on different dates never overlap.
        """
        if self.__date != other.get_date():
            return False
        return (self.__start_dt < other._TimeSlot__end_dt and
                other._TimeSlot__start_dt < self.__end_dt)

    def is_in_past(self) -> bool:
        """Return True if the slot's datetime is before current time."""
        return self.get_end_datetime() < datetime.now()

    def hours_until_start(self) -> float:
        """Return the number of hours from now until the start of this slot."""
        start_full = self.get_start_datetime()
        delta = start_full - datetime.now()
        return delta.total_seconds() / 3600

    def to_csv_values(self) -> tuple[str, str, str, float]:
        """
        Return a tuple of (date, start_time, end_time, duration_hours)
        for CSV serialisation.
        """
        return (self.__date, self.__start_time,
                self.__end_time, self.get_duration_hours())

    @classmethod
    def from_csv(cls, date: str, start_time: str, end_time: str) -> "TimeSlot":
        """Reconstruct a TimeSlot from CSV-stored strings."""
        return cls(date, start_time, end_time)

    def __str__(self) -> str:
        return (f"{self.__date} | {self.__start_time} – {self.__end_time} "
                f"({self.get_duration_hours():.1f} hr(s))")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TimeSlot):
            return False
        return (self.__date == other.__date and
                self.__start_time == other.__start_time and
                self.__end_time == other.__end_time)

    def __repr__(self) -> str:
        return (f"TimeSlot(date='{self.__date}', "
                f"start='{self.__start_time}', end='{self.__end_time}')")