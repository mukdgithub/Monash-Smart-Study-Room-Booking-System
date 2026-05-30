"""
Controller class responsible for booking creation, cancellation, and conflict detection.
"""

import csv
import os
import uuid
from datetime import datetime, date



from entity.booking import Booking
from entity.time_slot import TimeSlot
from entity.room import Room
from entity.user import User
from controller.optional_equipment_manager import OptionalEquipmentManager


class BookingManager:
    """Manages bookings including creation, conflict detection, and cancellation."""

    BOOKINGS_FILE = os.path.join(os.path.dirname(__file__), "../data/bookings.csv")
    MAX_ACTIVE_BOOKINGS = 3

    HEADERS = [
        "booking_id", "user_id", "room_id", "date", "start_time",
        "end_time", "duration_hours", "optional_equipment",
        "total_fee", "status", "deal_instance_id", "created_at", "checked_in_at"
    ]

    def __init__(self):
        self.__bookings: list[Booking] = []
        self.__oe_manager = OptionalEquipmentManager()
        self.__load_bookings()

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def __load_bookings(self):
        """
        Load bookings from CSV.
        TimeSlot is reconstructed from stored date/time fields.
        Optional equipment IDs are resolved to OptionalEquipment objects.
        """
        self.__bookings = []
        path = os.path.abspath(self.BOOKINGS_FILE)
        if not os.path.exists(path):
            return
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    time_slot = TimeSlot.from_csv(
                        row["date"], row["start_time"], row["end_time"]
                    )
                except ValueError:
                    continue  # skip malformed rows

                # Resolve comma-separated equipment IDs to objects
                oe_ids_str = row.get("optional_equipment", "")
                oe_ids     = [eid.strip() for eid in oe_ids_str.split(",") if eid.strip()]
                oe_objects = self.__oe_manager.find_equipment_by_ids(oe_ids)

                b = Booking(
                    booking_id=row["booking_id"],
                    user_id=row["user_id"],
                    room_id=row["room_id"],
                    time_slot=time_slot,
                    optional_equipment=oe_objects,
                    total_fee=float(row["total_fee"]),
                    status=row["status"],
                    deal_instance_id=row.get("deal_instance_id", ""),
                    created_at=row.get("created_at", ""),
                    checked_in_at=row.get("checked_in_at", "")
                )
                self.__bookings.append(b)

    def save_bookings(self):
        """Persist all bookings to CSV."""
        path = os.path.abspath(self.BOOKINGS_FILE)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADERS)
            for b in self.__bookings:
                writer.writerow(b.to_csv_row())

    def __generate_booking_id(self) -> str:
        return "B" + str(uuid.uuid4())[:8].upper()

    # ------------------------------------------------------------------ #
    #  Public methods                                                        #
    # ------------------------------------------------------------------ #

    def calculate_fee(self, room: Room, time_slot: TimeSlot,
                      selected_equipment: list = None,
                      deal_discount: float = 0.0) -> float:
        """
        Calculate total booking fee.

        Fee = (room hourly rate × duration) + equipment deposit (if any) - deal discount

        The equipment deposit is a flat $100 charged once per booking if ANY
        optional equipment is selected, regardless of the number of items chosen.
        No mixing of payment methods is allowed — the deposit is always charged
        as part of the total fee regardless of which payment method is used.
        """
        room_fee = room.get_price_per_hour() * time_slot.get_duration_hours()
        deposit  = Booking.EQUIPMENT_DEPOSIT if selected_equipment else 0.0
        total    = room_fee + deposit - deal_discount
        return max(0.0, total)

    def check_conflict(self, room_id: str, time_slot: TimeSlot) -> bool:
        """
        Return True if the given TimeSlot conflicts with any existing active booking
        for the same room. Uses TimeSlot.overlaps_with() and Booking.ACTIVE_STATUSES.
        """
        for b in self.__bookings:
            if (b.get_room_id() == room_id and
                    b.get_status() in Booking.ACTIVE_STATUSES):
                if time_slot.overlaps_with(b.get_time_slot()):
                    return True
        return False

    def validate_booking_input(self, room: Room,
                               time_slot: TimeSlot) -> tuple[bool, str]:
        """
        Validate a TimeSlot against room type rules and opening hours.
        Returns (is_valid, error_message).
        All time-related data comes from the TimeSlot entity.
        """
        if time_slot.is_in_past():
            return False, "Booking date cannot be in the past."

        duration = time_slot.get_duration_hours()
        if duration < 0.5:
            return False, "Minimum booking duration is 30 minutes."

        # Maximum duration per room type
        MAX_DURATION = {"small": 4.0, "medium": 8.0, "large": 8.0}
        room_type = room.get_room_type()
        max_duration = MAX_DURATION.get(room_type, 4.0)
        if duration > max_duration:
            return False, (f"{room_type.capitalize()} rooms cannot be booked "
                           f"for more than {max_duration:.0f} hours at a time.")

        hours_until = time_slot.hours_until_start()

        if room_type == "medium":
            if hours_until < 3:
                return False, "Medium rooms must be booked at least 3 hours in advance."
            if duration < 2:
                return False, "Medium rooms require a minimum booking of 2 hours."

        if room_type == "large":
            if hours_until < 24:
                return False, "Large rooms must be booked at least 24 hours in advance."
            if duration < 2:
                return False, "Large rooms require a minimum booking of 2 hours."

        opening = datetime.strptime(room.get_opening_time(), "%H:%M").time()
        closing = datetime.strptime(room.get_closing_time(), "%H:%M").time()
        if (time_slot.get_start_datetime().time() < opening or
                time_slot.get_end_datetime().time() > closing):
            return False, (f"Room is only available "
                           f"{room.get_opening_time()} – {room.get_closing_time()}.")

        return True, ""

    def get_active_bookings_count(self, user_id: str) -> int:
        """Return number of currently active/ongoing bookings for a user."""
        return sum(1 for b in self.__bookings
                   if b.get_user_id() == user_id
                   and b.get_status() in Booking.ACTIVE_STATUSES)

    def create_booking(self, user: User, room: Room, time_slot: TimeSlot,
                       optional_equipment: list, total_fee: float,
                       deal_applied: str = "") -> tuple[bool, str, Booking | None]:
        """
        Create and persist a new booking.
        Accepts a TimeSlot entity rather than raw date/time strings.
        deal_applied holds the UserDeal instance ID if paid by deal, else "".
        Returns (success, message, booking_object).
        """
        if self.get_active_bookings_count(user.get_user_id()) >= self.MAX_ACTIVE_BOOKINGS:
            return False, "You have reached the maximum of 3 active bookings.", None

        if not room.get_is_available():
            return False, f"Room {room.get_room_id()} is currently unavailable.", None

        if self.check_conflict(room.get_room_id(), time_slot):
            return False, "This room is already booked for the selected time slot.", None

        booking_id = self.__generate_booking_id()
        created_at = datetime.now().strftime("%d/%m/%Y %H:%M")
        booking = Booking(
            booking_id=booking_id,
            user_id=user.get_user_id(),
            room_id=room.get_room_id(),
            time_slot=time_slot,
            optional_equipment=optional_equipment,
            total_fee=total_fee,
            status=Booking.STATUS_ACTIVE,
            deal_instance_id=deal_applied,   # stores UserDeal instance ID or ""
            created_at=created_at
        )
        self.__bookings.append(booking)
        self.save_bookings()
        return True, "Booking confirmed!", booking

    def cancel_booking(self, booking: Booking,
                       room: Room, user: User) -> tuple[float, str, bool]:
        """
        Cancel a booking and calculate refund.

        Refund rules for the ROOM FEE portion:
          Small  : Late cancel (<0.5 hr before) → 50% of room fee refunded.
                   No-show (after start)         → 20% of room fee refunded.
          Medium : Late cancel (<3 hrs before)   → 50% of room fee refunded.
                   No-show                        → 0%  of room fee refunded.
          Large  : Late cancel (<4 hrs before)   → 30% of room fee refunded.
                   No-show                        → 0%  of room fee refunded.

        Equipment deposit ($100) is ALWAYS fully refunded on cancellation,
        regardless of timing, room type, or reason for cancellation.

        Returns (total_refund_amount, note_message,is_late).
        """
        room_refund = 1  # default: full room fee refunded
        late_note = ""
        late = False

        if booking.get_time_slot().hours_until_start() + booking.get_time_slot().get_duration_hours() <= 0:
            return 0.0, "This booking has already ended and cannot be cancelled.",late

        if booking.get_status() == Booking.STATUS_CANCELLED:
            return 0.0, "This booking is already cancelled.",late

        hours_until = booking.get_time_slot().hours_until_start()
        # total_fee   = booking.get_total_fee()
        room_type   = room.get_room_type()

        # Separate deposit from room fee
        deposit  = Booking.EQUIPMENT_DEPOSIT if booking.has_equipment() else 0.0
        room_fee = booking.get_total_fee() - deposit

        # NEWBIE20: room fee was $0 — no room fee to refund, only deposit
        if room_fee <= 0:
            room_refund = 0.0
            late_note   = "This booking was paid with NEWBIE20 Promo."

        elif room_type == "small":
            if hours_until < 0:
                room_refund = 0.2
                late_note   = "No-show: 80% of room fee forfeited."
                late = True
            elif hours_until < 0.5:
                room_refund = 0.5
                late_note   = "Late cancellation: 50% of room fee refunded."
                late = True

        elif room_type == "medium":
            if hours_until < 0:
                room_refund = 0.0
                late_note   = "No-show: full room fee forfeited."
                late = True
            elif hours_until < 3:
                room_refund = 0.5
                late_note   = "Late cancellation: 50% of room fee refunded."
                late = True

        elif room_type == "large":
            if hours_until < 0:
                room_refund = 0.0
                late_note   = "No-show: full room fee forfeited."
                late = True
            elif hours_until < 4:
                room_refund = 0.3
                late_note   = "Late cancellation: 30% of room fee refunded."
                late = True

        # Deposit always fully returned
        # total_refund = room_refund
        if deposit > 0:
            deposit_note = f" Equipment deposit of ${deposit:.2f} fully refunded."
            late_note    = (late_note + deposit_note).strip()

        booking.set_status(Booking.STATUS_CANCELLED)
        self.save_bookings()
        return room_refund, late_note, late

    # def is_late_cancellation(self, booking: Booking, room: Room) -> bool:
    #     """
    #     Return True if cancelling now counts as a strike-worthy late cancellation.
    #     Strike applies only to small rooms cancelled within 30 minutes of start.
    #     """
    #     hours_until = booking.get_time_slot().hours_until_start()
    #     return room.get_room_type() == "small" and 0 <= hours_until < 0.5

    # ------------------------------------------------------------------ #
    #  Check-in methods                                                     #
    # ------------------------------------------------------------------ #

    def request_check_in(self, booking: Booking) -> tuple[bool, str]:
        """
        Student requests check-in for their booking.

        Check-in window rules:
          - Available from 10 minutes BEFORE the booking start time
          - NOT available after the booking end time has passed
          - Only allowed when status is ACTIVE

        Returns (success, message).
        """
        if booking.get_status() != Booking.STATUS_ACTIVE:
            return False, (f"Cannot request check-in. "
                           f"Booking status is {booking.get_status()}.")

        ts                = booking.get_time_slot()
        hours_until_start = ts.hours_until_start()
        hours_until_end   = hours_until_start + ts.get_duration_hours()

        # Too early — more than 10 minutes before start
        CHECK_IN_EARLY_WINDOW_HOURS = 10 / 60
        if hours_until_start > CHECK_IN_EARLY_WINDOW_HOURS:
            minutes_remaining = int(hours_until_start * 60 - 10)
            return False, (
                f"Check-in is not available yet. "
                f"You can check in from 10 minutes before your session starts "
                f"({booking.get_start_time()} on {booking.get_date()}). "
                f"Please try again in {minutes_remaining} minute(s)."
            )

        # Too late — session has ended
        if hours_until_end <= 0:
            return False, (
                f"Check-in is no longer available. "
                f"Your booking session ended at {booking.get_end_time()}."
            )

        booking.set_status(Booking.STATUS_CHECK_IN_REQUESTED)
        checked_in_at = datetime.now().strftime("%d/%m/%Y %H:%M")
        booking.set_checked_in_at(checked_in_at)
        self.save_bookings()
        return True, "Check-in request submitted. Awaiting admin approval."

    def approve_check_in(self, booking: Booking) -> tuple[bool, str]:
        """
        Admin approves a student's check-in request.
        Returns (success, message).
        """
        if booking.get_status() != Booking.STATUS_CHECK_IN_REQUESTED:
            return False, (f"Cannot approve. "
                           f"Booking status is {booking.get_status()}.")
        booking.set_status(Booking.STATUS_CHECKED_IN)
        self.save_bookings()
        return True, f"Check-in approved for booking {booking.get_booking_id()}."

    def override_status(self, booking: Booking,
                        new_status: str) -> tuple[bool, str]:
        """
        Admin overrides a booking status to one of:
        ACTIVE, CHECKED_IN, CANCELLED, NO_SHOW, COMPLETED.
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
            return False, (f"Invalid status '{new_status}'. "
                           f"Allowed: {', '.join(sorted(allowed))}")
        old_status = booking.get_status()
        booking.set_status(new_status)
        self.save_bookings()
        return True, (f"Booking {booking.get_booking_id()} status changed "
                      f"from {old_status} to {new_status}.")

    def resolve_no_shows(self) -> tuple[list[Booking], list[Booking]]:
        """
        Scan all bookings whose session end time has passed and
        automatically resolve their status based on check-in state.

        Resolution rules:
          ACTIVE             → NO_SHOW   (never requested check-in)
          CHECK_IN_REQUESTED → NO_SHOW   (requested but not approved
                                          before session ended)
          CHECKED_IN         → COMPLETED (student was confirmed present)

        Returns:
          (no_show_list, completed_list)
        """
        no_shows  = []
        completed = []

        for b in self.__bookings:
            ts              = b.get_time_slot()
            hours_until_end = ts.hours_until_start() + ts.get_duration_hours()

            if hours_until_end > 0:
                continue

            if b.get_status() in (Booking.STATUS_ACTIVE,
                                  Booking.STATUS_CHECK_IN_REQUESTED):
                b.set_status(Booking.STATUS_NO_SHOW)
                no_shows.append(b)

            elif b.get_status() == Booking.STATUS_CHECKED_IN:
                b.set_status(Booking.STATUS_COMPLETED)
                completed.append(b)

        if no_shows or completed:
            self.save_bookings()

        return no_shows, completed

    def get_all_bookings_for_admin(self) -> list[Booking]:
        """Return all bookings in the system (admin use)."""
        return list(self.__bookings)

    def get_pending_check_ins(self) -> list[Booking]:
        """Return all bookings with CHECK_IN_REQUESTED status."""
        return [b for b in self.__bookings
                if b.get_status() == Booking.STATUS_CHECK_IN_REQUESTED]

    def get_active_bookings_for_room(self, room_id: str) -> list[Booking]:
        """Return all active/ongoing bookings for a given room."""
        return [b for b in self.__bookings
                if b.get_room_id() == room_id
                and b.get_status() in Booking.ACTIVE_STATUSES]

    def get_user_active_bookings(self, user_id: str) -> list[Booking]:
        """Return all active/ongoing bookings for a user."""
        return [b for b in self.__bookings
                if b.get_user_id() == user_id
                and b.get_status() in Booking.ACTIVE_STATUSES]

    def get_user_all_bookings(self, user_id: str) -> list[Booking]:
        """Return all bookings (all statuses) for a user."""
        return [b for b in self.__bookings if b.get_user_id() == user_id]

    def find_booking_by_id(self, booking_id: str) -> Booking | None:
        """Find a booking by its ID."""
        for b in self.__bookings:
            if b.get_booking_id() == booking_id:
                return b
        return None

    def get_booking_summary(self, room, time_slot: TimeSlot,
                            selected_equipment: list,
                            total_fee: float,
                            user_fund_balance: float) -> dict:
        """
        Build and return a booking summary dictionary before payment confirmation.
        Summary logic lives here in BookingManager, not in the boundary class.
        No booking is saved and no payment is deducted at this stage.

        Returns a dict with all summary fields ready for display.
        """
        equipment_names = (
            ", ".join(e.get_name() for e in selected_equipment)
            if selected_equipment else "None"
        )
        deposit  = Booking.EQUIPMENT_DEPOSIT if selected_equipment else 0.0
        room_fee = total_fee - deposit

        return {
            "room_id":        room.get_room_id(),
            "room_type":      room.get_room_type().capitalize(),
            "location":       room.get_location(),
            "standard_equip": room.get_standard_equipment(),
            "optional_equip": equipment_names,
            "deposit":        deposit,
            "room_fee":       room_fee,
            "date":           time_slot.get_date(),
            "start_time":     time_slot.get_start_time(),
            "end_time":       time_slot.get_end_time(),
            "duration_hours": time_slot.get_duration_hours(),
            "total_fee":      total_fee,
            "fund_balance":   user_fund_balance,
        }

    def get_activity_records(self, user_id: str) -> list:
        """
        Return a list of BookingActivityRecord objects for a user,
        sorted chronologically by date and time.
        """
        from entity.booking_activity_record import BookingActivityRecord

        bookings = self.get_user_all_bookings(user_id)
        records  = [BookingActivityRecord.from_booking(b) for b in bookings]

        def sort_key(r: BookingActivityRecord):
            try:
                return datetime.strptime(
                    f"{r.get_date()} {r.get_time()}", "%d/%m/%Y %H:%M"
                )
            except ValueError:
                return datetime.min

        records.sort(key=sort_key)
        return records