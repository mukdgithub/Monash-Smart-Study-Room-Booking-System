"""
Boundary class for the Booking Management screens.
"""

from datetime import datetime

from boundary.ui_utils import (print_header, get_menu_choice, DIVIDER, pause,
                               get_non_empty_input)
from controller.booking_manager import BookingManager
from controller.room_manager import RoomManager
from controller.user_manager import UserManager
from controller.payment_processor import PaymentProcessor, InsufficientFundsException
from controller.deal_package_manager import DealPackageManager
from controller.user_deal_manager import UserDealManager
from controller.optional_equipment_manager import OptionalEquipmentManager
from entity.time_slot import TimeSlot
from entity.user import User
from entity.room import Room
from entity.booking import Booking


class BookingMenu:
    """Handles all booking-related screens for students."""

    def __init__(self, user_manager: UserManager,
                 booking_manager: BookingManager,
                 room_manager: RoomManager,
                 deal_package_manager: DealPackageManager,
                 user_deal_manager: UserDealManager,
                 payment_processor: PaymentProcessor,
                 oe_manager: OptionalEquipmentManager):
        self.__user_manager         = user_manager
        self.__booking_manager      = booking_manager
        self.__room_manager         = room_manager
        self.__deal_package_manager = deal_package_manager
        self.__user_deal_manager    = user_deal_manager
        self.__payment_processor    = payment_processor
        self.__oe_manager           = oe_manager

    def show(self, user: User):
        """Display the Booking Management menu."""
        while True:
            print_header("Manage Booking Screen")
            print("\nBooking Management.")
            print("Manage your booking with the menu below.")
            choice = get_menu_choice([
                "Make booking",
                "View your current bookings",
                "View booking history",
                "Check in to booking",
                "Cancel booking",
                "Back to Home"
            ])
            if choice == 1:
                self.__make_booking_flow(user)
            elif choice == 2:
                self.__view_current_bookings(user)
            elif choice == 3:
                self.__view_booking_history(user)
            elif choice == 4:
                self.__check_in_flow(user)
            elif choice == 5:
                self.__cancel_booking_flow(user)
            elif choice == 6:
                return

    # ------------------------------------------------------------------ #
    #  Make booking                                                         #
    # ------------------------------------------------------------------ #

    def __make_booking_flow(self, user: User):
        """Top-level make-booking screen: browse/filter then book."""
        if user.get_is_suspended():
            print_header()
            print(f"\n  Your account is suspended until {user.get_suspension_end()}.")
            print("  You cannot make new bookings.")
            get_menu_choice(["Back to Booking Management"])
            return

        while True:
            print_header("Make Booking Screen")
            available = self.__room_manager.get_available_rooms()
            print(f"\n  ({len(available)} room(s) available)")
            self.__display_room_list(available)
            choice = get_menu_choice([
                "Filter room",
                "Choose a room to book",
                "Back to Booking Management"
            ])
            if choice == 1:
                filtered = self.__filter_flow(available)
                if filtered is not None:
                    self.__choose_and_book(user, filtered)
                    return
            elif choice == 2:
                self.__choose_and_book(user, available)
                return
            elif choice == 3:
                return

    def __filter_flow(self, rooms: list[Room]) -> list[Room] | None:
        """
        Display filter room screen and return filtered list.
        Filter logic delegated to RoomManager.view_room_by_filtering().
        """
        while True:
            print_header("Filter Room Screen")
            print()
            print("  Apply filters (press Enter to skip each filter):")

            max_price_raw  = input("  Max price per hour ($): ").strip()
            min_cap_raw    = input("  Minimum capacity (people): ").strip()
            room_type_raw  = input("  Room type (small / medium / large): ").strip().lower()
            location_kw    = input("  Location keyword: ").strip()
            equipment_kw   = input("  Equipment keyword (e.g. projector, whiteboard): ").strip()

            max_price = None
            if max_price_raw:
                try:
                    max_price = float(max_price_raw)
                except ValueError:
                    print("  Invalid price — filter ignored.")

            min_cap = None
            if min_cap_raw:
                try:
                    min_cap = int(min_cap_raw)
                except ValueError:
                    print("  Invalid capacity — filter ignored.")

            room_type  = room_type_raw if room_type_raw in ["small", "medium", "large"] else None
            location   = location_kw   if location_kw   else None
            equipment  = equipment_kw  if equipment_kw  else None

            filtered = self.__room_manager.view_room_by_filtering(
                rooms,
                max_price=max_price,
                min_capacity=min_cap,
                room_type=room_type,
                location_keyword=location,
                equipment_keyword=equipment
            )

            print_header("Filter Room Result Screen")
            if not filtered:
                print("\n  No rooms match the selected criteria.")
                print(f"\n{DIVIDER}")
                choice = get_menu_choice([
                    "Clear filters and show all rooms",
                    "Try different filters",
                    "Back to Make Booking"
                ])
                if choice == 1:
                    return rooms
                elif choice == 2:
                    continue
                else:
                    return None

            print(f"\n  ({len(filtered)} room(s) found)")
            self.__display_room_list(filtered)
            print(f"\n{DIVIDER}")
            choice = get_menu_choice([
                "Choose a room to book",
                "Clear filters and show all rooms",
                "Back to Make Booking"
            ])
            if choice == 1:
                return filtered
            elif choice == 2:
                return rooms
            else:
                return None

    def __choose_and_book(self, user: User, rooms: list[Room]):
        """Choose a room, enter date/time, select equipment, confirm and pay."""
        # --- Step 1: choose room ---
        while True:
            print_header("Choose a Room to Book Screen")
            self.__display_room_list(rooms)
            print()
            room_id = input("  > Enter Room ID: ").strip().upper()
            room = self.__room_manager.find_room_by_id(room_id)
            if not room or room not in rooms:
                print("  You entered an Invalid Room ID. Please re-enter.")
                continue
            break

        # --- Step 2: choose date and time ---
        time_slot = None
        while True:
            print_header("Choose a Room to Book - Date & Time Screen")
            print(f"\n  Room: {room}")
            print(f"  Opening: {room.get_opening_time()} – {room.get_closing_time()}")
            date_str  = input("  > Enter Date (dd/mm/yyyy): ").strip()
            start_str = input("  > Start time (HH:MM): ").strip()
            end_str   = input("  > End time   (HH:MM): ").strip()

            try:
                time_slot = TimeSlot(date_str, start_str, end_str)
            except ValueError as e:
                print(f"  {e}")
                continue

            valid, err = self.__booking_manager.validate_booking_input(room, time_slot)
            if not valid:
                print(f"  {err}")
                choice = get_menu_choice([
                    "Try again",
                    "Cancel and back to Choose a Room to Book"
                ])
                if choice == 2:
                    return
                continue

            if self.__booking_manager.check_conflict(room.get_room_id(), time_slot):
                print("  This room is already booked for the selected time slot.")
                choice = get_menu_choice([
                    "Try again",
                    "Cancel and back to Choose a Room to Book"
                ])
                if choice == 2:
                    return
                continue
            break

        # --- Step 2b: optional equipment ---
        selected_equipment = self.__select_equipment(time_slot)

        total_fee = self.__booking_manager.calculate_fee(
            room, time_slot, selected_equipment
        )

        # --- Step 3: booking summary ---
        while True:
            summary = self.__booking_manager.get_booking_summary(
                room, time_slot, selected_equipment,
                total_fee, user.get_fund_balance()
            )
            print_header("Booking Summary Screen")
            print(f"\n  Room ID             : {summary['room_id']}")
            print(f"  Room Type           : {summary['room_type']}")
            print(f"  Location            : {summary['location']}")
            print(f"  Standard Equipment  : {summary['standard_equip']}")
            print(f"  Optional Equipment  : {summary['optional_equip']}")
            print(f"  Booked Date         : {summary['date']}")
            print(f"  Booked Time         : {summary['start_time']} – {summary['end_time']}")
            print(f"  Duration            : {summary['duration_hours']:.1f} hour(s)")
            print(f"  Room fee            : ${summary['room_fee']:.2f}")
            if summary['deposit'] > 0:
                print(f"  Equipment deposit   : ${summary['deposit']:.2f} "
                      f"(fully refundable on cancellation)")
            print(f"  Total charged       : ${summary['total_fee']:.2f}")
            print(f"  Your current fund   : ${summary['fund_balance']:.2f}")
            print(f"\n{DIVIDER}")
            choice = get_menu_choice([
                "Go to payment",
                "Add fund",
                "Cancel Booking and Back to Booking Management"
            ])
            if choice == 3:
                return
            if choice == 2:
                from boundary.account_menu import AccountMenu
                am = AccountMenu(self.__user_manager)
                am._AccountMenu__add_fund(user)
                continue

            # --- Step 4: payment ---
            result = self.__payment_flow(user, room, time_slot,
                                         selected_equipment, total_fee)
            if result:
                return

    def __payment_flow(self, user: User, room: Room, time_slot: TimeSlot,
                       selected_equipment: list, total_fee: float) -> bool:
        """
        Handle payment screen including promo code and deal package.
        Returns True if booking was completed (or intentionally cancelled).
        """
        current_fee    = total_fee
        newbie_applied = False

        # Resolve eligible UserDeal instances for this booking upfront
        eligible_deals = self.__user_deal_manager.get_eligible_deals_for_booking(
            user.get_user_id(), room.get_room_type(), self.__deal_package_manager
        )

        while True:
            print_header("Payment Screen")
            print(f"\n  Total price for your booking : ${current_fee:.2f}")
            print(f"  Your current fund            : ${user.get_fund_balance():.2f}")
            balance_after = user.get_fund_balance() - current_fee
            print(f"  Your fund balance after payment: ${max(0, balance_after):.2f}")

            # Show eligible deal instances
            if eligible_deals and not newbie_applied:
                print(f"\n  Your eligible deal package(s):")
                for ud in eligible_deals:
                    pkg = self.__deal_package_manager.find_deal_by_id(
                        ud.get_deal_package_id()
                    )
                    pkg_name = pkg.get_name() if pkg else ud.get_deal_package_id()
                    suffix = ("✓ enough hours" if ud.get_hours_remaining() >= time_slot.get_duration_hours()
                              else "✗ insufficient hours — fund will be used instead")
                    print(f"    [{ud.get_deal_instance_id()}] {pkg_name} "
                          f"| {ud.get_hours_remaining():.1f} hrs remaining  {suffix}")
                print(f"  (The first deal with sufficient hours will be applied automatically)")
            else:
                print("\n  Deal package: None")

            print(f"\n{DIVIDER}")
            choice = get_menu_choice([
                "Confirm Payment",
                "Use Promo Code",
                "Cancel Booking and Back to Booking Management"
            ])

            if choice == 3:
                return True

            if choice == 2:
                code = input("\n  Please enter your promo code: ").strip().upper()
                if code == "NEWBIE20":
                    eligible, msg = self.__payment_processor.apply_newbie_promo(
                        user, room.get_room_type()
                    )
                    if eligible:
                        print_header("Promo Code Applied Screen")
                        print("\n  Great news! You've got a NEWBIE promotion.")
                        print("  This promotion is applicable to the first booking")
                        print("  of a newly registered account.")
                        print("  When you apply this promotion, the total booking fee will be $0.")
                        print(f"\n{DIVIDER}")
                        promo_choice = get_menu_choice([
                            "Apply the promotion and confirm payment",
                            "Back to payment"
                        ])
                        if promo_choice == 1:
                            current_fee    = 0.0
                            newbie_applied = True
                    else:
                        if user.get_newbie_used():
                            print_header()
                            print("\n  Your NEWBIE Promo code is exhausted.")
                            print("  You cannot use this NEWBIE Promo code anymore.")
                        else:
                            print_header()
                            print(f"\n  {msg}")
                        print(f"\n{DIVIDER}")
                        get_menu_choice(["Go back to payment"])
                else:
                    print_header("Incorrect Promo Code Screen")
                    print("\n  The promotion code you entered was incorrect.")
                    print(f"\n{DIVIDER}")
                    get_menu_choice(["Go back to payment"])
                continue

            # --- Confirm Payment ---
            # Pick the first eligible UserDeal with sufficient hours (if not newbie)
            selected_deal = None
            if not newbie_applied:
                for ud in eligible_deals:
                    if ud.get_hours_remaining() >= time_slot.get_duration_hours():
                        selected_deal = ud
                        break

            # Pre-flight fund check before creating any booking record
            deal_instance_id = selected_deal.get_deal_instance_id() if selected_deal else ""
            if not selected_deal and user.get_fund_balance() < current_fee:
                print_header("Insufficient Balance Screen")
                print("\n  Insufficient Balance")
                print("  You do not have enough funds to complete this payment.")
                print(f"  Current Fund    : ${user.get_fund_balance():.2f}")
                print(f"  Required Amount : ${current_fee:.2f}")
                print(f"\n{DIVIDER}")
                ib_choice = get_menu_choice([
                    "Add Funds and retry payment",
                    "Cancel Booking and Back to Booking Management"
                ])
                if ib_choice == 1:
                    from boundary.account_menu import AccountMenu
                    am = AccountMenu(self.__user_manager,
                                     self.__user_deal_manager,
                                     self.__deal_package_manager)
                    am._AccountMenu__add_fund(user)
                    continue  # loop back to payment confirmation screen
                return True  # user cancelled — no booking created

            # Create booking — only reached when funds are confirmed sufficient
            success, msg, booking = self.__booking_manager.create_booking(
                user=user, room=room, time_slot=time_slot,
                optional_equipment=selected_equipment,
                total_fee=current_fee, deal_applied=deal_instance_id
            )
            if not success:
                print_header()
                print(f"\n  {msg}")
                get_menu_choice(["Back to Booking Management"])
                return True

            # Process payment
            try:
                self.__payment_processor.execute_payment(
                    user, booking, selected_deal
                )
            except InsufficientFundsException:
                # Rollback: cancel the booking that was just saved
                booking.set_status(Booking.STATUS_CANCELLED)
                self.__booking_manager.save_bookings()
                print_header("Insufficient Balance Screen")
                print("\n  Insufficient Balance")
                print("  You do not have enough funds to complete this payment.")
                print(f"  Current Fund    : ${user.get_fund_balance():.2f}")
                print(f"  Required Amount : ${current_fee:.2f}")
                print(f"\n{DIVIDER}")
                get_menu_choice(["Back to Booking Management"])
                return True

            # Mark newbie used
            if newbie_applied:
                user.set_newbie_used(True)
                self.__user_manager.save_user(user)

            # Success screen
            print_header("Confirm Booking Screen")
            print("\n  Congratulations! Your booking is completed.")
            print("  Please see below for your booking receipt.\n")
            print(f"  Booking ID    : {booking.get_booking_id()}")
            print(f"  Room Number   : {room.get_room_id()}")
            print(f"  Room Type     : {room.get_room_type().capitalize()}")
            print(f"  Location      : {room.get_location()}")
            print(f"  Equipment     : {room.get_standard_equipment()}")
            if selected_equipment:
                oe_names = ", ".join(e.get_name() for e in selected_equipment)
                print(f"  Optional Equip: {oe_names}")
                deposit  = Booking.EQUIPMENT_DEPOSIT
                room_fee = current_fee - deposit
                print(f"  Room fee      : ${room_fee:.2f}")
                print(f"  Equipment dep : ${deposit:.2f} "
                      f"(fully refundable on cancellation)")
            print(f"  Booked Date   : {time_slot.get_date()}")
            print(f"  Booked Time   : {time_slot.get_start_time()} – {time_slot.get_end_time()}")
            print(f"  Total charged : ${current_fee:.2f}")
            print(f"  Remaining fund: ${user.get_fund_balance():.2f}")
            if selected_deal:
                print(f"  Deal used     : {selected_deal.get_deal_instance_id()} "
                      f"({selected_deal.get_hours_remaining():.1f} hrs remaining)")
            print(f"\n{DIVIDER}")
            get_menu_choice(["Back to Booking Management"])
            return True

    # ------------------------------------------------------------------ #
    #  View bookings                                                        #
    # ------------------------------------------------------------------ #

    def __view_current_bookings(self, user: User):
        print_header("View Your Current Bookings Screen")
        bookings = self.__booking_manager.get_user_active_bookings(user.get_user_id())
        if not bookings:
            print("\n  You have no active bookings.")
        else:
            print()
            for b in bookings:
                print(f"  [{b.get_booking_id()}] Room {b.get_room_id()} | "
                      f"{b.get_date()} {b.get_start_time()}–{b.get_end_time()} | "
                      f"${b.get_total_fee():.2f} | {b.get_status()}")
        print(f"\n{DIVIDER}")
        choice = get_menu_choice([
            "Cancel booking",
            "Back to Booking Management"
        ])
        if choice == 1:
            self.__cancel_booking_flow(user)

    def __view_booking_history(self, user: User):
        print_header("View Booking History Screen")
        bookings = self.__booking_manager.get_user_all_bookings(user.get_user_id())
        if not bookings:
            print("\n  No booking history found.")
        else:
            print()
            for b in bookings:
                print(f"  [{b.get_booking_id()}] Room {b.get_room_id()} | "
                      f"{b.get_date()} {b.get_start_time()}–{b.get_end_time()} | "
                      f"${b.get_total_fee():.2f} | {b.get_status()}")
        print(f"\n{DIVIDER}")
        get_menu_choice(["Go back to Booking Management"])

    # ------------------------------------------------------------------ #
    #  Cancel booking                                                       #
    # ------------------------------------------------------------------ #

    def __cancel_booking_flow(self, user: User):
        print_header("Cancel Booking Screen")
        bookings = self.__booking_manager.get_user_active_bookings(user.get_user_id())
        if not bookings:
            print("\n  You have no active bookings to cancel.")
            print(f"\n{DIVIDER}")
            get_menu_choice(["Back to Booking Management"])
            return

        print()
        for b in bookings:
            print(f"  [{b.get_booking_id()}] Room {b.get_room_id()} | "
                  f"{b.get_date()} {b.get_start_time()}–{b.get_end_time()} | "
                  f"${b.get_total_fee():.2f}")

        print()
        booking_id = input("  > Enter the Booking ID to cancel: ").strip().upper()
        booking    = self.__booking_manager.find_booking_by_id(booking_id)

        if not booking or booking.get_user_id() != user.get_user_id():
            print("  Invalid Booking ID. Returning to Booking Management.")
            pause()
            return

        room = self.__room_manager.find_room_by_id(booking.get_room_id())

        # Confirm cancellation
        print_header("Confirm Cancel Booking Screen")
        print("\n  You are cancelling the following booking:")
        print(f"\n  Booking ID : {booking.get_booking_id()}")
        print(f"  Room       : {booking.get_room_id()}")
        print(f"  Date       : {booking.get_date()}")
        print(f"  Time       : {booking.get_start_time()} – {booking.get_end_time()}")
        print(f"  Total paid : ${booking.get_total_fee():.2f}")
        if booking.has_equipment():
            deposit  = Booking.EQUIPMENT_DEPOSIT
            room_fee = booking.get_total_fee() - deposit
            print(f"    Room fee  : ${room_fee:.2f}")
            print(f"    Deposit   : ${deposit:.2f} (always fully refunded)")
        print(f"\n{DIVIDER}")
        choice = get_menu_choice([
            "Confirm cancelling",
            "Cancel cancelling and Back to Booking Management"
        ])
        if choice == 2:
            return

        # Resolve UserDeal instance if booking was paid by deal
        user_deal = None
        if booking.was_paid_by_deal():
            user_deal = self.__user_deal_manager.find_instance_by_id(
                booking.get_deal_instance_id()
            )

        # Process cancellation
        refund, note, late = self.__booking_manager.cancel_booking(booking, room, user)
        # late      = self.__booking_manager.is_late_cancellation(booking, room)
        suspended = False
        if late:
            suspended = self.__user_manager.add_strike(user)

        if refund > 0 or booking.was_paid_by_deal():
            self.__payment_processor.execute_refund(user, booking, refund, user_deal)

        # Display result screen
        deposit  = Booking.EQUIPMENT_DEPOSIT if booking.has_equipment() else 0.0
        total_fee = booking.get_total_fee()
        room_fee  = total_fee - deposit
        room_fee_refunded = room_fee * refund  # refund is a multiplier (0–1)
        total_refunded    = room_fee_refunded + deposit

        # Room-type-aware late-cancellation threshold for strike message (BKG-006)
        room_type = room.get_room_type() if room else "small"
        strike_threshold = {
            "small":  "30 minutes",
            "medium": "3 hours",
            "large":  "4 hours",
        }.get(room_type, "30 minutes")

        if suspended:
            print_header("Confirm Cancel Booking Screen")
            print("\n  !!Attention!!")
            print("  You now have reached 3 strikes.")
            print("  You will be suspended from booking rooms for 3 months.")
            print(f"  Strike occur when you cancel your booking less than "
                  f"{strike_threshold} in advance.")
        elif late:
            print_header("Confirm Cancel Booking Screen")
            print(f"\n  Your booking for Room {booking.get_room_id()} on "
                  f"{booking.get_date()}, {booking.get_start_time()} has been cancelled.")
            print(f"  You have {user.get_strike_count()} strike(s) for late cancellation.")
            print(f"  Strike occurs when you cancel less than {strike_threshold} in advance.")
            print("  When you have 3 strikes, you will be suspended for 3 months.")
        else:
            print_header("Confirm Cancel Booking Screen")
            print(f"\n  Your booking for Room {booking.get_room_id()} on "
                  f"{booking.get_date()}, {booking.get_start_time()} "
                  f"has been cancelled without strike.")

        if note:
            print(f"\n  Note: {note}")

        if booking.was_paid_by_deal():
            hours_restored = booking.get_duration_hours() * refund
            print(f"\n  Deal hours restored : {hours_restored:.1f} hr(s) "
                  f"to deal {booking.get_deal_instance_id()}")
            if booking.has_equipment():
                print(f"  Equipment deposit refunded to fund: ${Booking.EQUIPMENT_DEPOSIT:.2f}")
        elif booking.has_equipment():
            print(f"\n  Refund breakdown:")
            print(f"    Room fee refund   : ${room_fee_refunded:.2f}")
            print(f"    Equipment deposit : ${deposit:.2f} (fully refunded)")
            print(f"    Total refund      : ${total_refunded:.2f}")
        else:
            print(f"\n  Booking refund amount : ${room_fee_refunded:.2f}")

        print(f"  Remaining fund balance: ${user.get_fund_balance():.2f}")
        print(f"\n{DIVIDER}")
        get_menu_choice(["Go back to Booking Management"])

    # ------------------------------------------------------------------ #
    #  Check in                                                             #
    # ------------------------------------------------------------------ #

    def __check_in_flow(self, user: User):
        """
        Student requests check-in for an active booking.
        Check-in window: available from 10 minutes before session start.
        """
        print_header("Check In Screen")
        bookings    = self.__booking_manager.get_user_active_bookings(user.get_user_id())
        active_only = [b for b in bookings if b.get_status() == Booking.STATUS_ACTIVE]

        if not active_only:
            print("\n  You have no bookings available for check-in.")
            print(f"\n{DIVIDER}")
            get_menu_choice(["Back to Booking Management"])
            return

        CHECK_IN_WINDOW = 10 / 60
        in_window = []
        upcoming  = []
        expired   = []

        for b in active_only:
            ts = b.get_time_slot()
            hours_until_start = ts.hours_until_start()
            hours_until_end   = hours_until_start + ts.get_duration_hours()
            if hours_until_end < 0:
                expired.append(b)
            elif hours_until_start <= CHECK_IN_WINDOW:
                in_window.append(b)
            else:
                upcoming.append(b)

        print("\n  Your current bookings:\n")
        print(f"  {'Booking ID':<12} {'Room':<6} {'Date':<12} "
              f"{'Time':<16} {'Status':<10} {'Check-in'}")
        print("  " + "-" * 72)

        for b in in_window:
            print(f"  {b.get_booking_id():<12} {b.get_room_id():<6} "
                  f"{b.get_date():<12} "
                  f"{b.get_start_time()}–{b.get_end_time():<10} "
                  f"{b.get_status():<10} ✓ Available now")
        for b in upcoming:
            ts   = b.get_time_slot()
            mins = int(ts.hours_until_start() * 60 - 10)
            print(f"  {b.get_booking_id():<12} {b.get_room_id():<6} "
                  f"{b.get_date():<12} "
                  f"{b.get_start_time()}–{b.get_end_time():<10} "
                  f"{b.get_status():<10} Available in ~{mins} min(s)")
        for b in expired:
            print(f"  {b.get_booking_id():<12} {b.get_room_id():<6} "
                  f"{b.get_date():<12} "
                  f"{b.get_start_time()}–{b.get_end_time():<10} "
                  f"{b.get_status():<10} Session ended")

        if not in_window:
            print(f"\n  No bookings are currently within the check-in window.")
            print("  Check-in opens 10 minutes before your session starts.")
            print(f"\n{DIVIDER}")
            get_menu_choice(["Back to Booking Management"])
            return

        print()
        booking_id = input("  > Enter Booking ID to check in: ").strip().upper()
        booking    = self.__booking_manager.find_booking_by_id(booking_id)

        if not booking or booking.get_user_id() != user.get_user_id():
            print("  Invalid Booking ID.")
            pause()
            return

        if booking not in in_window:
            print("  That booking is not yet in the check-in window.")
            print("  Check-in opens 10 minutes before your session starts.")
            pause()
            return

        success, msg = self.__booking_manager.request_check_in(booking)
        print_header("Check In Screen")
        if success:
            print(f"\n  Check-in request submitted successfully!")
            print(f"  Booking ID : {booking.get_booking_id()}")
            print(f"  Room       : {booking.get_room_id()}")
            print(f"  Date       : {booking.get_date()}")
            print(f"  Time       : {booking.get_start_time()} – {booking.get_end_time()}")
            print(f"  Requested  : {booking.get_checked_in_at()}")
            print(f"\n  Your check-in is pending admin approval.")
        else:
            print(f"\n  Check-in failed.")
            print(f"  Reason: {msg}")
        print(f"\n{DIVIDER}")
        get_menu_choice(["Back to Booking Management"])

    # ------------------------------------------------------------------ #
    #  Helpers                                                              #
    # ------------------------------------------------------------------ #

    def __select_equipment(self, time_slot: TimeSlot) -> list:
        """
        Display optional equipment units available for the chosen time slot
        and let the student select any number of them.
        """
        all_bookings = self.__booking_manager.get_all_bookings_for_admin()
        available    = self.__oe_manager.get_available_equipment_for_slot(
            time_slot, all_bookings
        )

        if not available:
            print("\n  No optional equipment is available for this time slot.")
            return []

        print_header("Optional Equipment Selection Screen")
        print(f"\n  Available equipment for "
              f"{time_slot.get_date()} "
              f"{time_slot.get_start_time()}\u2013{time_slot.get_end_time()}:\n")
        print(f"  Note: A flat ${Booking.EQUIPMENT_DEPOSIT:.0f} deposit is charged "
              f"if you select any equipment,")
        print(f"        regardless of how many items you choose.")
        print(f"        The deposit is always fully refunded on cancellation.\n")
        print(f"  {'ID':<8} {'Name':<22} {'Description'}")
        print("  " + "-" * 62)
        for e in available:
            print(f"  {e.get_equipment_id():<8} {e.get_name():<22} "
                  f"{e.get_description()}")

        print("\n  Enter equipment IDs separated by commas (e.g. OE001,OE003)")
        raw = input("  > Your selection (or Enter to skip): ").strip()

        if not raw:
            return []

        selected = []
        ids = [i.strip().upper() for i in raw.split(",") if i.strip()]
        for eid in ids:
            item = next((e for e in available if e.get_equipment_id() == eid), None)
            if item:
                if item not in selected:
                    selected.append(item)
            else:
                print(f"  Warning: '{eid}' is not available "
                      f"for this time slot and was skipped.")

        if selected:
            names = ", ".join(e.get_name() for e in selected)
            print(f"\n  Selected  : {names}")
            print(f"  Deposit   : ${Booking.EQUIPMENT_DEPOSIT:.2f} "
                  f"(fully refundable on cancellation)")

        return selected

    def __display_room_list(self, rooms: list[Room]):
        """Print a formatted room list."""
        if not rooms:
            print("  No rooms available.")
            return
        print(f"\n  {'ID':<6} {'Type':<8} {'Capacity':<10} "
              f"{'Price/hr':<10} {'Location'}")
        print("  " + "-" * 60)
        for r in rooms:
            print(f"  {r.get_room_id():<6} {r.get_room_type().capitalize():<8} "
                  f"{r.get_capacity_str():<10} "
                  f"${r.get_price_per_hour():<9.2f} {r.get_location()}")