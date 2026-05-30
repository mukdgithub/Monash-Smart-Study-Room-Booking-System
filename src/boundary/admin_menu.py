"""
Boundary class for Admin screens (room management).
"""
from datetime import datetime
from boundary.ui_utils import print_header, get_menu_choice, DIVIDER, pause
from controller.room_manager import RoomManager
from controller.booking_manager import BookingManager
from controller.check_in_manager import CheckInManager
from controller.optional_equipment_manager import OptionalEquipmentManager
from controller.user_manager import UserManager
from controller.payment_processor import PaymentProcessor
from controller.user_deal_manager import UserDealManager
from entity.user import User
from entity.room import Room
from entity.booking import Booking


class AdminMenu:
    """Handles all admin-facing room management screens."""

    def __init__(self, room_manager: RoomManager,
                 booking_manager: BookingManager,
                 check_in_manager: CheckInManager,
                 oe_manager: OptionalEquipmentManager,
                 user_manager: UserManager,
                 payment_processor: PaymentProcessor,
                 user_deal_manager: UserDealManager):

        self.__room_manager      = room_manager
        self.__booking_manager   = booking_manager
        self.__check_in_manager  = check_in_manager
        self.__oe_manager        = oe_manager
        self.__se_manager        = room_manager.get_se_manager()
        self.__user_manager      = user_manager
        self.__payment_processor = payment_processor
        self.__user_deal_manager = user_deal_manager

    def show(self, user: User):
        """Display the Manage Room screen."""
        if not user.is_admin():
            print("\n  Access Denied: Admin features only.")
            pause()
            return

        while True:
            print_header("Admin Operation Screen")
            print("\nAdmin Operation.")
            choice = get_menu_choice([
                "View, Create, Update, or Delete Room",
                "Manage students' bookings",
                "Manage room availability",
                "Manage room pricing",
                "Manage standard equipment",
                "Manage optional equipment",
                "Back to main menu"
            ], show_home=False)
            if choice == 1:
                self.__crud_menu()
            elif choice == 2:
                self.__booking_menu()
            elif choice == 3:
                self.__availability_menu()
            elif choice == 4:
                self.__pricing_menu()
            elif choice == 5:
                self.__standard_equipment_menu()
            elif choice == 6:
                self.__equipment_menu()
            elif choice == 7:
                return

    # ------------------------------------------------------------------ #
    #  CRUD Room                                                              #
    # ------------------------------------------------------------------ #

    def __crud_menu(self):
        while True:
            print_header("View, Create, Update, Delete Room Screen")
            print("\nManage the Room with the options below.")
            choice = get_menu_choice([
                "View all rooms",
                "Register new rooms",
                "Update existing rooms",
                "Delete existing rooms from the system",
                "Back to Manage Room"
            ])
            if choice == 1:
                self.__view_all_room()
            elif choice == 2:
                self.__register_room()
            elif choice == 3:
                self.__update_room()
            elif choice == 4:
                self.__delete_room()
            elif choice == 5:
                return

    def __view_all_room(self):
        all_rooms = self.__room_manager.get_all_rooms()
        print_header("View All Room Screen\n")
        print(DIVIDER + "\n")
        for room in all_rooms:
            print(room)
        get_menu_choice(["Back to room management"])


    def __register_room(self):
        print_header("Register New Room Screen")
        print("\nAdd Room.")
        print("Add details of the room to be registered.\n")
        room_type = input("  > Enter Room Type (small/medium/large): ").strip().lower()
        if room_type not in Room.VALID_TYPES:
            print(f"  Invalid room type. Must be: {', '.join(Room.VALID_TYPES)}")
            pause()
            return

        location = input("  > Enter Location: ").strip()
        if not location:
            print("  Location cannot be empty.")
            pause()
            return

        # Show the equipment that will be auto-assigned
        spec = Room.STANDARD_EQUIPMENT[room_type]
        spec_str = ", ".join(f"{qty} x {name}" for name, qty in spec.items())

        print_header("Confirm Register New Room Screen")
        print(f"\n  Type      : {room_type.capitalize()}")
        print(f"  Capacity  : {Room.CAPACITIES[room_type]}")
        print(f"  Location  : {location}")
        print(f"  Equipment : {spec_str}")
        print(f"  Price/hr  : ${self.__room_manager.PRICES[room_type]:.2f}")
        print(f"\n{'-'*38}")
        choice = get_menu_choice([
            "Confirm New Room Registration",
            "Cancel and back to Room Management"
        ])
        if choice == 2:
            return

        success, result = self.__room_manager.add_room(room_type, location)
        if not success:
            print_header()
            print(f"\n  Error: {result}")
            print(f"\n{'-'*38}")
            get_menu_choice(["Go back to Room Management"])
            return

        room_id = result

        # Auto-assign standard equipment based on room type spec
        items = [(name, qty) for name, qty in spec.items()]
        self.__se_manager.add_equipment_bulk(room_id, items)
        self.__room_manager.refresh_room_equipment(room_id)

        print_header("Room Registered Successfully Screen")
        room = self.__room_manager.find_room_by_id(room_id)
        print(f"\n  Room {room_id} has been successfully registered.")
        if room:
            print(f"  Type      : {room.get_room_type().capitalize()}")
            print(f"  Location  : {room.get_location()}")
            print(f"  Equipment : {room.get_standard_equipment()}")
            print(f"  Price/hr  : ${room.get_price_per_hour():.2f}")
        print(f"\n{'-'*38}")
        get_menu_choice(["Go back to Room Management"])

    def __update_room(self):
        rooms = self.__room_manager.get_all_rooms()
        while True:
            print_header("Choose Room to be Updated Screen")
            print("\nUpdate Room")
            self.__display_rooms(rooms)
            room_id = input("\n  > Enter room ID to be updated or press Enter to exit: ").strip().upper()

            if not room_id:
                return

            room = self.__room_manager.find_room_by_id(room_id)
            if not room:
                print("  You entered incorrect Room ID, please re-enter.")
                continue
            break

        while True:
            print_header("Update Room Screen")
            print(f"\n  Updating room {room.get_room_id()} ({room.get_room_type().capitalize()})")
            choice = get_menu_choice([
                "Update location / opening / closing time",
                "Manage standard equipment",
                "Back to Room Management"
            ])
            if choice == 1:
                self.__update_room_details(room)
            elif choice == 2:
                self.__update_room_equipment(room)
            elif choice == 3:
                return

    def __update_room_details(self, room):
        """Update location, opening time, and closing time for a room."""
        print_header("Update Room Details Screen")
        print(f"\n  Updating room {room.get_room_id()}")
        print("  (Press Enter to keep current value)\n")
        new_loc = input(f"  > Location [{room.get_location()}]: ").strip()

        new_open = input(f"  > Opening time [{room.get_opening_time()}]: ").strip()
        if new_open:
            try:
                datetime.strptime(new_open, "%H:%M")
            except ValueError:
                print(f"  Invalid opening time '{new_open}'. Must be in HH:MM format (e.g. 09:00).")
                pause()
                return

        new_close = input(f"  > Closing time [{room.get_closing_time()}]: ").strip()
        if new_close:
            try:
                datetime.strptime(new_close, "%H:%M")
            except ValueError:
                print(f"  Invalid closing time '{new_close}'. Must be in HH:MM format (e.g. 22:00).")
                pause()
                return

        effective_open  = new_open  if new_open  else room.get_opening_time()
        effective_close = new_close if new_close else room.get_closing_time()
        if datetime.strptime(effective_open, "%H:%M") >= datetime.strptime(effective_close, "%H:%M"):
            print(f"  Closing time ({effective_close}) must be after opening time ({effective_open}).")
            pause()
            return

        success, msg = self.__room_manager.update_room(
            room.get_room_id(),
            location=new_loc if new_loc else None,
            opening_time=effective_open,
            closing_time=effective_close
        )
        print_header("Room Updated Screen")
        print(f"\n  {msg}")
        updated = self.__room_manager.find_room_by_id(room.get_room_id())
        if updated:
            print(f"  Location  : {updated.get_location()}")
            print(f"  Opens     : {updated.get_opening_time()}")
            print(f"  Closes    : {updated.get_closing_time()}")
            print(f"  Equipment : {updated.get_standard_equipment()}")
        print(f"\n{'-'*38}")
        get_menu_choice(["Go back to Room Management"])

    def __update_room_equipment(self, room):
        """Manage standard equipment for a room — assign from inventory or unassign to inventory."""
        room_id   = room.get_room_id()
        room_type = room.get_room_type()
        spec      = Room.STANDARD_EQUIPMENT[room_type]  # {name: max_qty}

        while True:
            print_header("Manage Room Equipment Screen")
            current_units = self.__se_manager.get_equipment_by_room(room_id)

            # Build current count per name
            current_counts: dict[str, int] = {}
            for u in current_units:
                current_counts[u.get_name()] = current_counts.get(u.get_name(), 0) + 1

            print(f"\n  Room {room_id} ({room_type.capitalize()}) — current equipment:\n")
            print(f"  {'ID':<8} {'Name':<22} {'Status'}")
            print("  " + "-" * 45)
            for u in current_units:
                print(f"  {u.get_equipment_id():<8} {u.get_name():<22} {u.get_status()}")

            print(f"\n  Allowed spec: "
                  + ", ".join(f"{qty} x {name}" for name, qty in spec.items()))

            choice = get_menu_choice([
                "Unassign a unit from this room to inventory",
                "Assign a unit from inventory to this room",
                "Back"
            ])

            if choice == 3:
                return

            elif choice == 1:
                # --- Unassign ---
                if not current_units:
                    print("\n  No equipment currently assigned to this room.")
                    pause()
                    continue

                eid = input("\n  > Enter equipment ID to unassign (or Enter to go back): ").strip().upper()
                if not eid:
                    continue

                item = self.__se_manager.find_by_id(eid)
                if not item or item.get_room_id() != room_id:
                    print(f"  Equipment '{eid}' not found in room {room_id}.")
                    pause()
                    continue

                success, msg = self.__se_manager.unassign_from_room(eid)
                if success:
                    self.__room_manager.refresh_room_equipment(room_id)
                print(f"\n  {msg}")
                pause()

            elif choice == 2:
                # --- Assign ---
                inventory = self.__se_manager.get_inventory()
                if not inventory:
                    print("\n  No equipment in inventory.")
                    pause()
                    continue

                # Filter inventory to only items whose name is in this room's spec
                valid_inventory = [
                    e for e in inventory if e.get_name() in spec
                ]
                if not valid_inventory:
                    print(f"\n  No inventory equipment matches the allowed spec for a "
                          f"{room_type} room.")
                    print(f"  Allowed types: {', '.join(spec.keys())}")
                    pause()
                    continue

                print(f"\n  Available inventory (spec-compatible):\n")
                print(f"  {'ID':<8} {'Name':<22} {'Status'}")
                print("  " + "-" * 45)
                for e in valid_inventory:
                    print(f"  {e.get_equipment_id():<8} {e.get_name():<22} {e.get_status()}")

                eid = input("\n  > Enter equipment ID to assign (or Enter to go back): ").strip().upper()
                if not eid:
                    continue

                item = self.__se_manager.find_by_id(eid)
                if not item or not item.is_in_inventory():
                    print(f"  Equipment '{eid}' not found in inventory.")
                    pause()
                    continue

                success, msg = self.__se_manager.assign_to_room(eid, room_id, room_type)
                if success:
                    self.__room_manager.refresh_room_equipment(room_id)
                print(f"\n  {msg}")
                pause()

    def __delete_room(self):
        rooms = self.__room_manager.get_all_rooms()
        while True:
            print_header("Choose Room to be Deleted Screen")
            self.__display_rooms(rooms)
            room_id = input("\n  > Enter room ID to be deleted or press Enter to exit: ").strip().upper()

            if not room_id:  # return to previous screen if users press Enter
                return

            room = self.__room_manager.find_room_by_id(room_id)
            if not room:
                print(
                    "  You entered incorrect room ID. Please re-enter.")
                continue
            break

        active_bookings = self.__booking_manager.get_active_bookings_for_room(room.get_room_id())
        if active_bookings:
            print_header("Active Bookings Detected Screen")
            print(f"\n  Room {room.get_room_id()} has {len(active_bookings)} active booking(s):\n")
            print(f"  {'Booking ID':<12} {'User ID':<10} {'Date':<12} {'Time':<14} {'Status'}")
            print("  " + "-" * 62)
            for b in active_bookings:
                print(f"  {b.get_booking_id():<12} {b.get_user_id():<10} "
                      f"{b.get_date():<12} "
                      f"{b.get_start_time()}–{b.get_end_time():<8} "
                      f"{b.get_status()}")
            print("\n  Proceeding will cancel all active bookings and refund affected students.")
            print(f"\n{'-' * 38}")
            choice = get_menu_choice([
                "Proceed with deletion (cancel bookings and refund students)",
                "Cancel and go back to Room Management"
            ])
            if choice == 2:
                return

        print_header("Confirm Deleting Room Screen")
        print(f"\n  Deleting Room {room.get_room_id()}:")
        print(f"    Room ID    : {room.get_room_id()}")
        print(f"    Type       : {room.get_room_type().capitalize()}")
        print(f"    Capacity   : {room.get_capacity_str()}")
        print(f"    Location   : {room.get_location()}")
        print(f"    Equipment  : {room.get_standard_equipment()}")
        print("\n  The room above will be permanently deleted. Are you sure?")
        print(f"\n{'-' * 38}")
        choice = get_menu_choice([
            "Confirm Room deleting",
            "Cancel and back to Manage room menu"
        ])
        if choice == 2:
            return

        # ---- Confirmed — NOW perform booking cancellations and refunds ----
        if active_bookings:
            print_header("Processing Cancellations Screen")
            for b in active_bookings:
                user = self.__user_manager.find_user_by_id(b.get_user_id())
                if not user:
                    continue
                refund, note, _ = self.__booking_manager.cancel_booking(b, room, user)
                b.set_status(Booking.STATUS_CANCELLED)
                if refund > 0:
                    deal = self.__user_deal_manager.find_instance_by_id(b.get_deal_instance_id())
                    self.__payment_processor.execute_refund(user, b, refund, deal)
                print(f"\n  Booking {b.get_booking_id()} (User: {b.get_user_id()})")
                print(f"    Status : CANCELLED")
                print(f"    {note}")
                if refund > 0:
                    print(f"    Refund : ${refund:.2f} → New balance: ${user.get_fund_balance():.2f}")
            self.__booking_manager.save_bookings()

        success, msg = self.__room_manager.delete_room(room_id)
        print_header("Confirm Deleting Room Screen")
        print(f"\n  {msg}")
        print(f"\n{'-' * 38}")
        get_menu_choice(["Go back to Room Management"])

    # ------------------------------------------------------------------ #
    #  Manage Booking                                                         #
    # ------------------------------------------------------------------ #

    def __booking_menu(self):
        """Admin booking management screen."""
        while True:
            print_header("Manage Bookings Screen")
            print("\nBooking Management.")
            # Resolve no-shows each time admin views bookings
            no_shows, completed = self.__check_in_manager.resolve_no_shows()
            for booking in no_shows:
                user = self.__user_manager.find_user_by_id(booking.get_user_id())
                room = self.__room_manager.find_room_by_id(booking.get_room_id())
                if user and room:
                    self.__payment_processor.execute_no_show_penalty(user, booking, room)
            if no_shows:
                print(f"\n  [{len(no_shows)} booking(s) marked NO_SHOW — penalties applied]")
            if completed:
                print(f"  [{len(completed)} booking(s) marked COMPLETED]")

            pending = self.__check_in_manager.get_pending_check_ins()
            print(f"  Pending check-in approvals: {len(pending)}")
            choice = get_menu_choice([
                "View all bookings",
                "View pending check-in requests",
                "Approve check-in request",
                "Override booking status",
                "Back to Admin Operation Screen"
            ])
            if choice == 1:
                self.__view_all_bookings()
            elif choice == 2:
                self.__view_pending_check_ins()
            elif choice == 3:
                self.__approve_check_in()
            elif choice == 4:
                self.__override_booking_status()
            elif choice == 5:
                return

    def __view_all_bookings(self):
        """View all bookings in the system."""
        print_header("View All Bookings Screen")
        bookings = self.__booking_manager.get_all_bookings_for_admin()
        if not bookings:
            print("\n  No bookings found in the system.")
        else:
            print(f"\n  {'Booking ID':<12} {'User ID':<10} {'Room':<6} "
                  f"{'Date':<12} {'Time':<14} {'Status'}")
            print("  " + "-" * 72)
            for b in bookings:
                print(f"  {b.get_booking_id():<12} {b.get_user_id():<10} "
                      f"{b.get_room_id():<6} {b.get_date():<12} "
                      f"{b.get_start_time()}–{b.get_end_time():<8} "
                      f"{b.get_status()}")
        print(f"\n{DIVIDER}")
        get_menu_choice(["Back to Manage Bookings"])

    def __view_pending_check_ins(self):
        """View all bookings with CHECK_IN_REQUESTED status."""
        print_header("Pending Check-in Requests Screen")
        pending = self.__check_in_manager.get_pending_check_ins()
        if not pending:
            print("\n  No pending check-in requests.")
        else:
            print(f"\n  {'Booking ID':<12} {'User ID':<10} {'Room':<6} "
                  f"{'Date':<12} {'Time':<14} {'Requested At'}")
            print("  " + "-" * 72)
            for b in pending:
                print(f"  {b.get_booking_id():<12} {b.get_user_id():<10} "
                      f"{b.get_room_id():<6} {b.get_date():<12} "
                      f"{b.get_start_time()}–{b.get_end_time():<8} "
                      f"{b.get_checked_in_at()}")
        print(f"\n{DIVIDER}")
        get_menu_choice(["Back to Manage Bookings"])

    def __approve_check_in(self):
        """Admin approves a student check-in request."""
        pending = self.__check_in_manager.get_pending_check_ins()
        if not pending:
            print_header()
            print("\n  No pending check-in requests to approve.")
            pause()
            return

        print_header("Approve Check-in Screen")
        print(f"\n  {'Booking ID':<12} {'User ID':<10} {'Room':<6} {'Date':<12} {'Time'}")
        print("  " + "-" * 60)
        for b in pending:
            print(f"  {b.get_booking_id():<12} {b.get_user_id():<10} "
                  f"{b.get_room_id():<6} {b.get_date():<12} "
                  f"{b.get_start_time()}–{b.get_end_time()}")

        print()
        booking_id = input("  > Enter Booking ID to approve: ").strip().upper()
        booking = self.__booking_manager.find_booking_by_id(booking_id)

        if not booking or booking.get_status() != Booking.STATUS_CHECK_IN_REQUESTED:
            print_header()
            print("  Invalid Booking ID or booking is not awaiting check-in.")
            pause()
            return

        success, msg = self.__check_in_manager.approve_check_in(booking)
        print_header("Check-in Approved Screen")
        print(f"\n  {msg}")
        print(f"  Student: {booking.get_user_id()}")
        print(f"  Room   : {booking.get_room_id()}")
        print(f"  Date   : {booking.get_date()} "
              f"{booking.get_start_time()}–{booking.get_end_time()}")
        print(f"\n{DIVIDER}")
        get_menu_choice(["Back to Manage Bookings"])

    def __override_booking_status(self):
        """
        Admin overrides a booking status.
        Allowed targets: ACTIVE, CHECKED_IN, CANCELLED, NO_SHOW, COMPLETED.
        When overriding to NO_SHOW or CANCELLED, the appropriate refund/penalty
        is applied via PaymentProcessor.
        """
        print_header("Override Booking Status Screen")
        booking_id = input("  > Enter Booking ID to override: ").strip().upper()
        booking = self.__booking_manager.find_booking_by_id(booking_id)

        if not booking:
            print_header()
            print(f"  Booking {booking_id} not found.")
            pause()
            return

        room = self.__room_manager.find_room_by_id(booking.get_room_id())
        user = self.__user_manager.find_user_by_id(booking.get_user_id())

        print(f"\n  Booking  : {booking.get_booking_id()}")
        print(f"  Student  : {booking.get_user_id()}")
        print(f"  Room     : {booking.get_room_id()}")
        print(f"  Date     : {booking.get_date()} "
              f"{booking.get_start_time()}–{booking.get_end_time()}")
        print(f"  Status   : {booking.get_status()}")
        print(f"  Total fee: ${booking.get_total_fee():.2f}")

        print(f"\n  Select new status:")
        status_options = [
            Booking.STATUS_ACTIVE,
            Booking.STATUS_CHECKED_IN,
            Booking.STATUS_CANCELLED,
            Booking.STATUS_NO_SHOW,
            Booking.STATUS_COMPLETED,
            "Cancel and go back"
        ]
        choice = get_menu_choice(status_options)
        if choice == len(status_options):
            return

        new_status = status_options[choice - 1]
        old_status = booking.get_status()

        # Confirm override
        print_header("Confirm Override Screen")
        print(f"\n  You are changing booking {booking.get_booking_id()}")
        print(f"  from {old_status} → {new_status}")
        confirm = get_menu_choice(["Confirm", "Cancel"])
        if confirm == 2:
            return

        refund       = 0.0
        penalty_note = ""
        msg          = ""

        if new_status == Booking.STATUS_CANCELLED and old_status in Booking.ACTIVE_STATUSES:
            # Use cancel_booking directly — calculates the refund, sets the
            # status to CANCELLED, and persists.  override_status must NOT be
            # called first, because it would set the status to CANCELLED before
            # cancel_booking runs, triggering cancel_booking's early-exit guard
            # and resulting in a $0 refund.
            if user and room:
                refund, penalty_note, is_late = self.__booking_manager.cancel_booking(
                    booking, room, user
                )

                deal = self.__user_deal_manager.find_instance_by_id(
                        booking.get_deal_instance_id()
                    )

                self.__payment_processor.execute_refund(user, booking, refund, deal)

            msg = f"Booking {booking.get_booking_id()} has been cancelled."

        else:
            # For all other target statuses (ACTIVE, CHECKED_IN, NO_SHOW, COMPLETED)
            # use override_status as a raw status change.
            success, msg = self.__check_in_manager.override_status(booking, new_status)
            if not success:
                print(f"\n  Error: {msg}")
                pause()
                return

            if new_status == Booking.STATUS_NO_SHOW and old_status in Booking.ACTIVE_STATUSES:
                if user and room:
                    refund, penalty_note = self.__payment_processor.execute_no_show_penalty(
                        user, booking, room
                    )

        print_header("Override Successful Screen")
        print(f"\n  {msg}")
        if penalty_note:
            print(f"  {penalty_note}")
        if refund > 0 and user:
            # 'refund' from cancel_booking is a percent (0.0–1.0); compute the
            # actual dollar amount issued so the admin sees a meaningful number.
            deposit = Booking.EQUIPMENT_DEPOSIT if booking.has_equipment() else 0.0
            room_fee = booking.get_total_fee() - deposit
            refund_dollars = room_fee * refund + deposit
            print(f"  Refund issued  : ${refund_dollars:.2f} ({int(refund * 100)}% of room fee)")
            print(f"  Student balance: ${user.get_fund_balance():.2f}")
        print(f"\n{DIVIDER}")
        get_menu_choice(["Back to Manage Bookings"])


    # ------------------------------------------------------------------ #
    #  Availability                                                         #
    # ------------------------------------------------------------------ #

    def __availability_menu(self):
        while True:
            print_header("Manage Room Suspension")
            print("\nManage room suspension with option below.")
            choice = get_menu_choice([
                "Suspend room",
                "Unsuspend room",
                "Back to Admin Operation Screen"
            ])
            if choice == 1:
                self.__suspend_room(suspend=True)
            elif choice == 2:
                self.__suspend_room(suspend=False)
            elif choice == 3:
                return

    def __suspend_room(self, suspend: bool):
        action = "suspend" if suspend else "unsuspend"
        all_rooms    = self.__room_manager.get_all_rooms()
        # Bug fix #2: restrict eligible pool to only rooms that actually need the action.
        # is_available == True  → room is currently active  → eligible to suspend.
        # is_available == False → room is currently suspended → eligible to unsuspend.
        target_rooms = [r for r in all_rooms if r.get_is_available() == suspend]

        print_header(f"{'Suspend' if suspend else 'Unsuspend'} Room Screen")
        if not target_rooms:
            print(f"\n  No rooms available to {action}.")
            pause()
            return

        self.__display_rooms(target_rooms)
        room_id = input(f"\n  > Enter room ID to {action}: ").strip().upper()

        # Bug fix #2: validate the entered ID against the eligible pool only,
        # not the full room list, so an already-suspended room cannot be re-suspended.
        eligible_ids = {r.get_room_id() for r in target_rooms}
        if room_id not in eligible_ids:
            print_header("Invalid Room ID Screen")
            if self.__room_manager.find_room_by_id(room_id):
                status_word = "already suspended" if suspend else "not suspended"
                print(f"\n  Room {room_id} is {status_word} and cannot be {action}ed.")
            else:
                print(f"\n  Room ID '{room_id}' does not exist.")
            print(f"\n{'-'*38}")
            get_menu_choice(["Back to Manage Room Suspension"])
            return

        room = self.__room_manager.find_room_by_id(room_id)

        # Bug fix #1: when suspending, cancel all active bookings for this room,
        # issue full refunds, and report each affected booking to the admin.
        affected = []
        if suspend:
            affected = self.__booking_manager.get_active_bookings_for_room(room_id)
            if affected:
                print(f"\n  WARNING: {len(affected)} active booking(s) will be cancelled:")
                print(f"  {'Booking ID':<12} {'User ID':<10} {'Date':<12} {'Time'}")
                print("  " + "-" * 52)
                for b in affected:
                    print(f"  {b.get_booking_id():<12} {b.get_user_id():<10} "
                          f"{b.get_date():<12} {b.get_start_time()}–{b.get_end_time()}")
                print(f"\n  All affected bookings will receive a full refund.")
                print(f"\n{'-'*38}")
                confirm = get_menu_choice([
                    "Confirm suspension and cancel affected bookings",
                    "Cancel and go back"
                ])
                if confirm == 2:
                    return

                # Cancel each booking and refund the user in full
                for b in affected:
                    user = self.__user_manager.find_user_by_id(b.get_user_id())
                    if user:
                        deal = self.__user_deal_manager.find_instance_by_id(
                            b.get_deal_instance_id()
                        )
                        # Full refund (100%) regardless of timing — room suspension
                        # is an admin action, not the student's fault.
                        self.__payment_processor.execute_refund(
                            user, b, refund_percent=1.0, user_deal=deal
                        )
                    b.set_status(Booking.STATUS_CANCELLED)
                self.__booking_manager.save_bookings()

        success, msg = self.__room_manager.set_room_availability(room_id, not suspend)
        print_header(f"Room {'Suspended' if suspend else 'Unsuspended'} Screen")
        print(f"\n  {msg}")
        if suspend and affected:
            print(f"  {len(affected)} booking(s) cancelled and fully refunded.")
        print(f"\n{'-'*38}")
        get_menu_choice(["Back to Manage Room"])

    # ------------------------------------------------------------------ #
    #  Pricing                                                              #
    # ------------------------------------------------------------------ #
    def __pricing_menu(self):
        """Pricing Management menu — stays open until user chooses 'Back'."""
        while True:
            print_header("Pricing Management Screen")
            choice = get_menu_choice([
                "View current pricing",
                "Update pricing",
                "Back to Admin Operation Screen"
            ])
            if choice == 1:
                self.__view_pricing_menu()
            elif choice == 2:
                self.__update_room_pricing()
            elif choice == 3:
                return

    def __view_pricing_menu(self):
        print_header("Pricing and Equipment Screen")
        print("\n  Current Room prices as follow: \n")
        for r in RoomManager.PRICES.keys():
            print(f"    {r} room : ${float(RoomManager.PRICES[r])} per hour")
        get_menu_choice(["Back to Pricing Management"])

    def __update_room_pricing(self):
        """Update room pricing by room size"""
        print_header("Update room pricing screen")
        while True:
            room_type = input(f"\n  > select room size to update the price ('small', 'medium', 'large'): ")
            if room_type.lower() not in RoomManager.PRICES.keys():
                print("  Invalid room type. Please select 'small', 'medium', 'large' only.")
            else:
                room_type = room_type.lower()
                break

        while True:
            new_price = input(f"\n  > Enter new room price: ")
            try:
                new_price = float(new_price)
            except ValueError:
                print("  Invalid room price. Please enter a positive number.")
                continue
            except TypeError:
                print("  Invalid room price. Please enter a positive number.")
                continue
            if new_price <= 0.0:
                print("  Invalid room price. Please enter a positive number.")
                continue
            break

        print(f"\n  {DIVIDER}")
        print(f"\nUpdating room pricing of {room_type} room, from {RoomManager.PRICES[room_type]} to {new_price}")

        choice = get_menu_choice(["confirm update","cancel update"])
        if choice == 1:
            self.__room_manager.update_room_price(room_type, new_price)
            print(f"\n  {DIVIDER}")
            print("Update room pricing completed.")
            pause()
        elif choice == 2:
            return

    # ------------------------------------------------------------------ #
    #  Standard Equipment menu                                             #
    # ------------------------------------------------------------------ #

    def __standard_equipment_menu(self):
        """Standard equipment management menu."""
        while True:
            print_header("Manage Standard Equipment Screen")
            choice = get_menu_choice([
                "View equipment by room",
                "View inventory",
                "Add equipment to inventory",
                "Assign inventory equipment to a room",
                "Unassign equipment from room to inventory",
                "Update equipment status",
                "Update equipment name",
                "Permanently delete equipment",
                "Back to Admin Operation Screen"
            ])
            if choice == 1:
                self.__se_view_by_room()
            elif choice == 2:
                self.__se_view_inventory()
            elif choice == 3:
                self.__se_add_to_inventory()
            elif choice == 4:
                self.__se_assign_to_room()
            elif choice == 5:
                self.__se_unassign_from_room()
            elif choice == 6:
                self.__se_update_status()
            elif choice == 7:
                self.__se_update_name()
            elif choice == 8:
                self.__se_delete()
            elif choice == 9:
                return

    def __se_view_by_room(self):
        print_header("View Standard Equipment by Room Screen")
        rooms = self.__room_manager.get_all_rooms()
        self.__display_rooms(rooms)
        room_id = input("\n  > Enter room ID to view equipment (or Enter to go back): ").strip().upper()
        if not room_id:
            return
        room = self.__room_manager.find_room_by_id(room_id)
        if not room:
            print(f"  Room '{room_id}' not found.")
            pause()
            return
        units = self.__se_manager.get_equipment_by_room(room_id)
        print_header(f"Equipment for Room {room_id}")
        if not units:
            print(f"\n  No standard equipment assigned to room {room_id}.")
        else:
            print(f"\n  {'ID':<8} {'Name':<22} {'Status'}")
            print("  " + "-" * 45)
            for e in units:
                print(f"  {e.get_equipment_id():<8} {e.get_name():<22} {e.get_status()}")
        print(f"\n{DIVIDER}")
        get_menu_choice(["Back to Manage Standard Equipment"])

    def __se_view_inventory(self):
        print_header("Inventory Screen")
        units = self.__se_manager.get_inventory()
        if not units:
            print("\n  No equipment currently in inventory.")
        else:
            print(f"\n  {'ID':<8} {'Name':<22} {'Status'}")
            print("  " + "-" * 45)
            for e in units:
                print(f"  {e.get_equipment_id():<8} {e.get_name():<22} {e.get_status()}")
        print(f"\n{DIVIDER}")
        get_menu_choice(["Back to Manage Standard Equipment"])

    def __se_add_to_inventory(self):
        print_header("Add Equipment to Inventory Screen")
        name = input("  > Enter equipment name: ").strip()
        if not name:
            print("  Equipment name cannot be empty.")
            pause()
            return
        success, result = self.__se_manager.add_equipment(room_id=None, name=name)
        print_header()
        if success:
            print(f"\n  Equipment '{name}' added to inventory with ID {result}.")
        else:
            print(f"\n  Error: {result}")
        print(f"\n{DIVIDER}")
        get_menu_choice(["Back to Manage Standard Equipment"])

    def __se_assign_to_room(self):
        print_header("Assign Equipment to Room Screen")
        inventory = self.__se_manager.get_inventory()
        if not inventory:
            print("\n  No equipment in inventory to assign.")
            pause()
            return
        print(f"\n  {'ID':<8} {'Name':<22} {'Status'}")
        print("  " + "-" * 45)
        for e in inventory:
            print(f"  {e.get_equipment_id():<8} {e.get_name():<22} {e.get_status()}")

        eid = input("\n  > Enter equipment ID to assign (or Enter to go back): ").strip().upper()
        if not eid:
            return
        item = self.__se_manager.find_by_id(eid)
        if not item or not item.is_in_inventory():
            print(f"  Equipment '{eid}' not found in inventory.")
            pause()
            return

        self.__display_rooms(self.__room_manager.get_all_rooms())
        room_id = input("\n  > Enter room ID to assign to (or Enter to go back): ").strip().upper()
        if not room_id:
            return
        if not self.__room_manager.find_room_by_id(room_id):
            print(f"  Room '{room_id}' not found.")
            pause()
            return

        # verify standard equipment type and quantity against the room spec
        room = self.__room_manager.find_room_by_id(room_id)
        room_type = room.get_room_type()

        success, msg = self.__se_manager.assign_to_room(eid, room_id, room_type)
        if success:
            self.__room_manager.refresh_room_equipment(room_id)
        print_header()
        print(f"\n  {msg}")
        print(f"\n{DIVIDER}")
        get_menu_choice(["Back to Manage Standard Equipment"])

    def __se_unassign_from_room(self):
        print_header("Unassign Equipment from Room Screen")
        rooms = self.__room_manager.get_all_rooms()
        self.__display_rooms(rooms)
        room_id = input("\n  > Enter room ID to unassign from (or Enter to go back): ").strip().upper()
        if not room_id:
            return
        if not self.__room_manager.find_room_by_id(room_id):
            print(f"  Room '{room_id}' not found.")
            pause()
            return

        units = self.__se_manager.get_equipment_by_room(room_id)
        if not units:
            print(f"\n  No equipment assigned to room {room_id}.")
            pause()
            return

        print(f"\n  {'ID':<8} {'Name':<22} {'Status'}")
        print("  " + "-" * 45)
        for e in units:
            print(f"  {e.get_equipment_id():<8} {e.get_name():<22} {e.get_status()}")

        eid = input("\n  > Enter equipment ID to move to inventory (or Enter to go back): ").strip().upper()
        if not eid:
            return

        success, msg = self.__se_manager.unassign_from_room(eid)
        if success:
            self.__room_manager.refresh_room_equipment(room_id)
        print_header()
        print(f"\n  {msg}")
        print(f"\n{DIVIDER}")
        get_menu_choice(["Back to Manage Standard Equipment"])

    def __se_update_status(self):
        print_header("Update Equipment Status Screen")
        all_units = self.__se_manager.get_all_equipment()
        if not all_units:
            print("\n  No standard equipment in the system.")
            pause()
            return

        print(f"\n  {'ID':<8} {'Name':<22} {'Location':<12} {'Status'}")
        print("  " + "-" * 58)
        for e in all_units:
            loc = e.get_room_id() if e.get_room_id() else "Inventory"
            print(f"  {e.get_equipment_id():<8} {e.get_name():<22} {loc:<12} {e.get_status()}")

        eid = input("\n  > Enter equipment ID to update (or Enter to go back): ").strip().upper()
        if not eid:
            return
        item = self.__se_manager.find_by_id(eid)
        if not item:
            print(f"  Equipment '{eid}' not found.")
            pause()
            return

        from entity.standard_equipment import StandardEquipment
        print(f"\n  Current status: {item.get_status()}")
        print(f"  Valid statuses: {', '.join(StandardEquipment.VALID_STATUSES)}")
        new_status = input("  > Enter new status: ").strip().lower()

        success, msg = self.__se_manager.update_status(eid, new_status)
        print_header()
        print(f"\n  {msg}")
        print(f"\n{DIVIDER}")
        get_menu_choice(["Back to Manage Standard Equipment"])

    def __se_update_name(self):
        print_header("Update Equipment Name Screen")
        all_units = self.__se_manager.get_all_equipment()
        if not all_units:
            print("\n  No standard equipment in the system.")
            pause()
            return

        print(f"\n  {'ID':<8} {'Name':<22} {'Location'}")
        print("  " + "-" * 45)
        for e in all_units:
            loc = e.get_room_id() if e.get_room_id() else "Inventory"
            print(f"  {e.get_equipment_id():<8} {e.get_name():<22} {loc}")

        eid = input("\n  > Enter equipment ID to rename (or Enter to go back): ").strip().upper()
        if not eid:
            return
        item = self.__se_manager.find_by_id(eid)
        if not item:
            print(f"  Equipment '{eid}' not found.")
            pause()
            return

        new_name = input(f"  > Enter new name [{item.get_name()}]: ").strip()
        if not new_name:
            print("  No changes made.")
            pause()
            return

        success, msg = self.__se_manager.update_name(eid, new_name)
        if success and item.get_room_id():
            self.__room_manager.refresh_room_equipment(item.get_room_id())
        print_header()
        print(f"\n  {msg}")
        print(f"\n{DIVIDER}")
        get_menu_choice(["Back to Manage Standard Equipment"])

    def __se_delete(self):
        print_header("Permanently Delete Equipment Screen")
        all_units = self.__se_manager.get_all_equipment()
        if not all_units:
            print("\n  No standard equipment in the system.")
            pause()
            return

        print(f"\n  {'ID':<8} {'Name':<22} {'Location':<12} {'Status'}")
        print("  " + "-" * 58)
        for e in all_units:
            loc = e.get_room_id() if e.get_room_id() else "Inventory"
            print(f"  {e.get_equipment_id():<8} {e.get_name():<22} {loc:<12} {e.get_status()}")

        eid = input("\n  > Enter equipment ID to permanently delete (or Enter to go back): ").strip().upper()
        if not eid:
            return
        item = self.__se_manager.find_by_id(eid)
        if not item:
            print(f"  Equipment '{eid}' not found.")
            pause()
            return

        print(f"\n  You are about to permanently delete:")
        print(f"    ID     : {item.get_equipment_id()}")
        print(f"    Name   : {item.get_name()}")
        loc = item.get_room_id() if item.get_room_id() else "Inventory"
        print(f"    Location: {loc}")
        print(f"    Status : {item.get_status()}")
        print(f"\n  This action cannot be undone.")
        print(f"\n{'-'*38}")
        choice = get_menu_choice(["Confirm permanent deletion", "Cancel"])
        if choice == 2:
            return

        room_id = item.get_room_id()
        success, msg = self.__se_manager.delete_equipment(eid)
        if success and room_id:
            self.__room_manager.refresh_room_equipment(room_id)
        print_header()
        print(f"\n  {msg}")
        print(f"\n{DIVIDER}")
        get_menu_choice(["Back to Manage Standard Equipment"])

    # ------------------------------------------------------------------ #
    #  Optional Equipment menu                                             #
    # ------------------------------------------------------------------ #

    def __equipment_menu(self):
        """Optional equipment CRUD menu."""
        while True:
            print_header("Manage Equipment Screen")
            choice = get_menu_choice([
                "View all equipment",
                "Add equipment",
                "Update equipment",
                "Delete equipment",
                "Back to Admin Operation Screen"
            ])
            if choice == 1:
                self.__view_all_equipment()
            elif choice == 2:
                self.__add_equipment()
            elif choice == 3:
                self.__update_equipment()
            elif choice == 4:
                self.__delete_equipment()
            elif choice == 5:
                return

    # --- Read ---
    def __view_all_equipment(self):
        print_header("View All Equipment Screen")
        items = self.__oe_manager.get_all_equipment()
        if not items:
            print("\n  No optional equipment registered in the system.")
        else:
            print(f"\n  {'ID':<8} {'Name':<22} {'Description'}")
            print("  " + "-" * 62)
            for e in items:
                print(f"  {e.get_equipment_id():<8} {e.get_name():<22} "
                      f"{e.get_description()}")

        print(f"\n{DIVIDER}")
        get_menu_choice(["Back to Manage Equipment"])

    # --- Create ---
    def __add_equipment(self):
        print_header("Add Equipment Screen")
        print("\nAdd Equipment.")
        while True:
            name = input("  Enter equipment name: ").strip()
            description = input("  Enter short description: ").strip()

            if not name:
                print_header("Invalid Equipment Information Screen")
                print("\n  Equipment name cannot be empty. Please re-enter.")
                continue

            success, result = self.__oe_manager.add_equipment(name, description)
            if success:
                print_header("Equipment Added Successfully Screen")
                print(f"\n  New Equipment '{name}' has been given an ID of {result}")
                print(f"  and is successfully registered.")
                print(f"\n{DIVIDER}")
                get_menu_choice(["Back to Manage Equipment"])
            else:
                print(f"\n  Error: {result}")
                pause()
            return

    # --- Update ---
    def __update_equipment(self):
        items = self.__oe_manager.get_all_equipment()
        if not items:
            print("\n  No equipment to update.")
            pause()
            return

        while True:
            print_header("Update Equipment Screen")
            print("\nUpdate Equipment.")
            self.__display_equipment(items)
            eid = input("\n  Enter ID of the equipment to be updated: ").strip().upper()
            item = self.__oe_manager.find_equipment_by_id(eid)
            if not item:
                print_header("Incorrect Equipment ID Screen")
                print("\n  The ID entered is incorrect. Please re-enter.")
                continue
            break

        print_header("Update Equipment Screen")
        print(f"\n  Updating equipment {item.get_name()} ({item.get_equipment_id()})")
        print("  (Press Enter to keep current value)\n")
        new_name = input(f"  Enter new equipment name [{item.get_name()}]: ").strip()
        new_desc = input(f"  Enter new short description [{item.get_description()}]: ").strip()

        success, msg = self.__oe_manager.update_equipment(
            eid,
            name=new_name if new_name else None,
            description=new_desc if new_desc else None
        )
        print_header("Equipment Updated Successfully Screen")
        print(f"\n  {msg}")
        print(f"\n{DIVIDER}")
        get_menu_choice(["Back to Manage Equipment"])

    # --- Delete ---
    def __delete_equipment(self):
        items = self.__oe_manager.get_all_equipment()
        if not items:
            print("\n  No equipment to delete.")
            pause()
            return

        while True:
            print_header("Delete Equipment Screen")
            print("\nDelete Equipment.")
            self.__display_equipment(items)
            eid = input("\n  Enter ID of the equipment to be deleted: ").strip().upper()
            item = self.__oe_manager.find_equipment_by_id(eid)
            if not item:
                print_header("Incorrect Equipment ID Screen")
                print("\n  The ID entered is incorrect. Please re-enter.")
                continue
            break

        # Confirmation screen — admin must explicitly approve before deletion
        print_header("Confirm Delete Equipment Screen")
        print(f"\n  You are about to permanently delete:")
        print(f"    ID         : {item.get_equipment_id()}")
        print(f"    Name       : {item.get_name()}")
        print(f"    Description: {item.get_description()}")
        print(f"\n  This action cannot be undone.")
        print(f"\n{DIVIDER}")
        choice = get_menu_choice([
            "Confirm permanent deletion",
            "Cancel and back to Manage Equipment"
        ])
        if choice == 2:
            return

        success, msg = self.__oe_manager.delete_equipment(eid)
        print_header("Equipment Deleted Successfully Screen")
        print(f"\n  {msg}")
        print(f"\n{DIVIDER}")
        get_menu_choice(["Back to Manage Equipment"])


    # ------------------------------------------------------------------ #
    #  Helper                                                               #
    # ------------------------------------------------------------------ #

    def __display_rooms(self, rooms: list[Room]):
        print(f"\n  {'ID':<6} {'Type':<8} {'Status':<12} {'Location'}")
        print("  " + "-" * 55)
        for r in rooms:
            status = "Available" if r.get_is_available() else "Suspended"
            print(f"  {r.get_room_id():<6} {r.get_room_type().capitalize():<8} "
                  f"{status:<12} {r.get_location()}")

    def __display_equipment(self, items):
        print(f"\n  {'ID':<8} {'Name':<22} {'Description'}")
        print("  " + "-" * 62)
        for e in items:
            print(f"  {e.get_equipment_id():<8} {e.get_name():<22} "
                  f"{e.get_description()}")