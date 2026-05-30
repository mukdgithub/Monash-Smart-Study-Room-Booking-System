"""
Policy class encapsulating all cancellation refund rules for the MSSRB system.

Extracted from BookingManager.cancel_booking() to satisfy OCP:
adding a new room type, or changing a refund threshold, requires
editing only this file.
"""

from entity.booking import Booking
from entity.room import Room


class CancellationPolicy:
    """
    Calculates the refund fraction and generates a human-readable note
    for a cancellation, based on room type and time remaining until the
    booking starts.

    Refund rules (room fee portion only):
      Small  : no-show (<0 hr)        → 20 % of room fee refunded
               late cancel (<0.5 hr)  → 50 % of room fee refunded
               otherwise              → 100 % of room fee refunded

      Medium : no-show (<0 hr)        →  0 % of room fee refunded
               late cancel (<3 hr)    → 50 % of room fee refunded
               otherwise              → 100 % of room fee refunded

      Large  : no-show (<0 hr)        →  0 % of room fee refunded
               late cancel (<4 hr)    → 30 % of room fee refunded
               otherwise              → 100 % of room fee refunded

    The equipment deposit ($100) is ALWAYS fully returned regardless of
    room type, timing, or reason.  That deposit note is appended to the
    returned message automatically when equipment was selected.
    """

    def calculate(
        self,
        booking: Booking,
        room: Room,
    ) -> tuple[float, str, bool]:
        """
        Determine the refund for a cancellation.

        Args:
            booking:  the Booking being cancelled
            room:     the Room the booking was for (provides room_type)

        Returns:
            (room_refund_fraction, note_message, is_late)
            where room_refund_fraction is applied to the room-fee portion only.

        Pre-conditions (callers must check before calling):
            - booking has not already ended
            - booking is not already CANCELLED
        """
        hours_until = booking.get_time_slot().hours_until_start()
        total_fee   = booking.get_total_fee()
        room_type   = room.get_room_type()
        deposit     = Booking.EQUIPMENT_DEPOSIT if booking.has_equipment() else 0.0

        # NEWBIE20 bookings have zero room fee — nothing to refund
        if total_fee - deposit <= 0:
            note = "This booking was paid with NEWBIE20 Promo."
            if deposit > 0:
                note += f" Equipment deposit of ${deposit:.2f} fully refunded."
            return 0.0, note.strip(), False

        room_refund = 1.0   # default: full refund
        late_note   = ""
        is_late     = False

        if room_type == "small":
            if hours_until < 0:
                room_refund = 0.2
                late_note   = "No-show: 80% of room fee forfeited."
                is_late     = True
            elif hours_until < 0.5:
                room_refund = 0.5
                late_note   = "Late cancellation: 50% of room fee refunded."
                is_late     = True

        elif room_type == "medium":
            if hours_until < 0:
                room_refund = 0.0
                late_note   = "No-show: full room fee forfeited."
                is_late     = True
            elif hours_until < 3:
                room_refund = 0.5
                late_note   = "Late cancellation: 50% of room fee refunded."
                is_late     = True

        elif room_type == "large":
            if hours_until < 0:
                room_refund = 0.0
                late_note   = "No-show: full room fee forfeited."
                is_late     = True
            elif hours_until < 4:
                room_refund = 0.3
                late_note   = "Late cancellation: 30% of room fee refunded."
                is_late     = True

        if deposit > 0:
            deposit_note = f" Equipment deposit of ${deposit:.2f} fully refunded."
            late_note    = (late_note + deposit_note).strip()

        return room_refund, late_note, is_late