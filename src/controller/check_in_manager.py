"""
Controller class responsible for the booking check-in lifecycle.

Extracted from BookingManager so that check-in concerns are isolated
and independently testable.
"""

from datetime import datetime

from entity.booking import Booking
from controller.booking_repository import BookingRepository


class CheckInManager:
    """
    Manages the complete check-in lifecycle for bookings:
      - Student requests check-in (within the allowed window)
      - Admin approves a check-in request
      - Automatic no-show / completion resolution after sessions end
      - Admin status overrides

    Depends only on BookingRepository for persistence — no knowledge of
    fees, validation rules, or room-type policy.
    """

    # Check-in becomes available this many hours before the session start
    CHECK_IN_EARLY_WINDOW_HOURS: float = 10 / 60   # 10 minutes

    def __init__(self, repository: BookingRepository):
        self.__repo = repository

    # ------------------------------------------------------------------ #
    #  Student-facing                                                       #
    # ------------------------------------------------------------------ #

    def request_check_in(self, booking: Booking) -> tuple[bool, str]:
        """
        Student requests check-in for their booking.

        Window rules:
          - Available from 10 minutes BEFORE the booking start time
          - NOT available after the booking end time has passed
          - Only allowed when status is ACTIVE

        Returns (success, message).
        """
        if booking.get_status() != Booking.STATUS_ACTIVE:
            return False, (
                f"Cannot request check-in. "
                f"Booking status is {booking.get_status()}."
            )

        ts                = booking.get_time_slot()
        hours_until_start = ts.hours_until_start()
        hours_until_end   = hours_until_start + ts.get_duration_hours()

        if hours_until_start > self.CHECK_IN_EARLY_WINDOW_HOURS:
            minutes_remaining = int(hours_until_start * 60 - 10)
            return False, (
                f"Check-in is not available yet. "
                f"You can check in from 10 minutes before your session starts "
                f"({booking.get_start_time()} on {booking.get_date()}). "
                f"Please try again in {minutes_remaining} minute(s)."
            )

        if hours_until_end <= 0:
            return False, (
                f"Check-in is no longer available. "
                f"Your booking session ended at {booking.get_end_time()}."
            )

        booking.set_status(Booking.STATUS_CHECK_IN_REQUESTED)
        booking.set_checked_in_at(datetime.now().strftime("%d/%m/%Y %H:%M"))
        self.__repo.save()
        return True, "Check-in request submitted. Awaiting admin approval."

    # ------------------------------------------------------------------ #
    #  Admin-facing                                                         #
    # ------------------------------------------------------------------ #

    def approve_check_in(self, booking: Booking) -> tuple[bool, str]:
        """
        Admin approves a student's check-in request.
        Returns (success, message).
        """
        if booking.get_status() != Booking.STATUS_CHECK_IN_REQUESTED:
            return False, (
                f"Cannot approve. "
                f"Booking status is {booking.get_status()}."
            )
        booking.set_status(Booking.STATUS_CHECKED_IN)
        self.__repo.save()
        return True, f"Check-in approved for booking {booking.get_booking_id()}."

    def override_status(self, booking: Booking,
                        new_status: str) -> tuple[bool, str]:
        """
        Admin overrides a booking to any valid terminal or active status.
        Allowed values: ACTIVE, CHECKED_IN, CANCELLED, NO_SHOW, COMPLETED.
        Returns (success, message).
        """
        allowed = {
            Booking.STATUS_ACTIVE,
            Booking.STATUS_CHECKED_IN,
            Booking.STATUS_CANCELLED,
            Booking.STATUS_NO_SHOW,
            Booking.STATUS_COMPLETED,
        }
        if new_status not in allowed:
            return False, (
                f"Invalid status '{new_status}'. "
                f"Allowed: {', '.join(sorted(allowed))}"
            )
        old_status = booking.get_status()
        booking.set_status(new_status)
        self.__repo.save()
        return True, (
            f"Booking {booking.get_booking_id()} status changed "
            f"from {old_status} to {new_status}."
        )

    def resolve_no_shows(self) -> tuple[list[Booking], list[Booking]]:
        """
        Scan all bookings whose session end time has passed and
        automatically finalise their status.

        Resolution rules:
          ACTIVE             → NO_SHOW   (never requested check-in)
          CHECK_IN_REQUESTED → NO_SHOW   (requested but not approved in time)
          CHECKED_IN         → COMPLETED (student was confirmed present)

        Returns (no_show_list, completed_list).
        """
        no_shows  = []
        completed = []

        for b in self.__repo.get_all():
            ts              = b.get_time_slot()
            hours_until_end = ts.hours_until_start() + ts.get_duration_hours()

            if hours_until_end > 0:
                continue   # session has not ended yet

            if b.get_status() in (Booking.STATUS_ACTIVE,
                                   Booking.STATUS_CHECK_IN_REQUESTED):
                b.set_status(Booking.STATUS_NO_SHOW)
                no_shows.append(b)

            elif b.get_status() == Booking.STATUS_CHECKED_IN:
                b.set_status(Booking.STATUS_COMPLETED)
                completed.append(b)

        if no_shows or completed:
            self.__repo.save()

        return no_shows, completed

    # ------------------------------------------------------------------ #
    #  Queries                                                              #
    # ------------------------------------------------------------------ #

    def get_pending_check_ins(self) -> list[Booking]:
        """Return all bookings currently awaiting admin check-in approval."""
        return [b for b in self.__repo.get_all()
                if b.get_status() == Booking.STATUS_CHECK_IN_REQUESTED]