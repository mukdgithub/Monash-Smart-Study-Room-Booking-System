"""
Boundary class for the main home menu (post-login).
"""

from boundary.ui_utils import print_header, get_menu_choice, ReturnToHomeException
from boundary.account_menu import AccountMenu
from boundary.booking_menu import BookingMenu
from boundary.deal_menu import DealMenu
from boundary.admin_menu import AdminMenu
from controller.user_manager import UserManager
from controller.booking_repository import BookingRepository
from controller.booking_manager import BookingManager
from controller.cancellation_policy import CancellationPolicy
from controller.check_in_manager import CheckInManager
from controller.room_manager import RoomManager
from controller.payment_processor import PaymentProcessor
from controller.deal_package_manager import DealPackageManager
from controller.user_deal_manager import UserDealManager
from controller.optional_equipment_manager import OptionalEquipmentManager
from entity.user import User


class MainMenu:
    """
    Home screen shown after a successful login.
    Role-based routing is implemented here and delegates to the correct menu class.

    Wiring order:
      1. Leaf dependencies (managers with no controller deps)
      2. BookingRepository  (needs OeManager)
      3. CancellationPolicy (no deps)
      4. BookingManager     (needs Repository + Policy + OeManager)
      5. CheckInManager     (needs Repository)
      6. Boundary menus
    """

    def __init__(self):
        # ── Leaf managers ──────────────────────────────────────────────
        self.__user_manager         = UserManager()
        self.__room_manager         = RoomManager()
        self.__deal_package_manager = DealPackageManager()
        self.__user_deal_manager    = UserDealManager()
        self.__oe_manager           = OptionalEquipmentManager()

        self.__payment_processor = PaymentProcessor(
            self.__user_manager, self.__user_deal_manager
        )

        # ── Booking subsystem ──────────────────────────────────────────
        self.__booking_repo   = BookingRepository(self.__oe_manager)
        self.__cancel_policy  = CancellationPolicy()
        self.__booking_manager = BookingManager(
            self.__booking_repo,
            self.__cancel_policy,
            self.__oe_manager,
        )
        self.__check_in_manager = CheckInManager(self.__booking_repo)

        # ── Boundary menus ─────────────────────────────────────────────
        self.__account_menu = AccountMenu(
            self.__user_manager,
            self.__user_deal_manager,
            self.__deal_package_manager,
        )
        self.__booking_menu = BookingMenu(
            self.__user_manager,
            self.__booking_manager,
            self.__check_in_manager,
            self.__room_manager,
            self.__deal_package_manager,
            self.__user_deal_manager,
            self.__payment_processor,
            self.__oe_manager,
        )
        self.__deal_menu = DealMenu(
            self.__deal_package_manager,
            self.__payment_processor,
            self.__user_manager,
        )
        self.__admin_menu = AdminMenu(
            self.__room_manager,
            self.__booking_manager,
            self.__check_in_manager,
            self.__oe_manager,
            self.__user_manager,
            self.__payment_processor,
            self.__user_deal_manager,
        )

    def show(self, user: User):
        """Display the home menu for the logged-in user."""
        while True:
            print_header("User Home Screen")
            print(f"\n  Welcome, {user.get_first_name()}!\n")

            if user.is_admin():
                options = [
                    "Manage My Account",
                    "Go to Admin Operation",
                    "Log out"
                ]
            else:
                options = [
                    "Manage My Account",
                    "Manage My Booking",
                    "View deal package",
                    "Log out"
                ]

            choice = get_menu_choice(options, show_home=False)

            try:
                if user.is_admin():
                    if choice == 1:
                        self.__account_menu.show(user)
                    elif choice == 2:
                        self.__admin_menu.show(user)
                    elif choice == 3:
                        print("\n  You have been logged out. Goodbye!")
                        return
                else:
                    if choice == 1:
                        self.__account_menu.show(user)
                    elif choice == 2:
                        self.__booking_menu.show(user)
                    elif choice == 3:
                        self.__deal_menu.show(user)
                    elif choice == 4:
                        print("\n  You have been logged out. Goodbye!")
                        return
            except ReturnToHomeException:
                pass  # loop back to home