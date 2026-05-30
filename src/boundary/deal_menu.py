"""
Boundary class for Deal Package screens.
"""

from boundary.ui_utils import print_header, get_menu_choice, DIVIDER
from controller.deal_package_manager import DealPackageManager
from controller.payment_processor import PaymentProcessor, InsufficientFundsException
from controller.user_manager import UserManager
from entity.user import User


class DealMenu:
    """Handles viewing and purchasing deal packages."""

    def __init__(self, deal_manager: DealPackageManager,
                 payment_processor: PaymentProcessor,
                 user_manager: UserManager):
        self.__deal_manager = deal_manager
        self.__payment_processor = payment_processor
        self.__user_manager = user_manager

    def show(self, user: User):
        """View deal packages and optionally buy one."""
        while True:
            print_header("View Deal Package Screen")
            deals = self.__deal_manager.get_available_deals()

            if not deals:
                print("\n  No deal packages are currently available.")
                print(f"\n{DIVIDER}")
                get_menu_choice(["Back to Main menu"], show_home=False)
                return

            print("\n  Available Deal Packages:\n")
            for d in deals:
                print(f"  [{d.get_deal_id()}] {d.get_name()}")
                print(f"         {d.get_description()}")
                print(f"         Price: ${d.get_price():.2f} | "
                      f"Hours: {d.get_bookable_hours()} | "
                      f"Room: {d.get_applicable_room_type().capitalize()} | "
                      f"Valid until: {d.get_valid_until()}")
                print()

            print(f"\n{DIVIDER}")
            choice = get_menu_choice([
                "Buy a deal",
                "Back to Home"
            ])
            if choice == 2:
                return

            self.__buy_deal_flow(user, deals)

    def __buy_deal_flow(self, user: User, deals):
        """Handle deal purchase."""
        print_header("Choose Deal Package Screen")
        print("\n  Available Deal Packages:\n")
        for d in deals:
            print(f"  [{d.get_deal_id()}] {d.get_name()}")

        deal_id = input("\n  Enter a deal ID to buy: ").strip().upper()
        deal = self.__deal_manager.find_deal_by_id(deal_id)

        if not deal:
            print_header()
            print(f"\n  Incorrect deal ID.")
            print(f"\n{DIVIDER}")
            get_menu_choice([
                "Back to choose deal package",
                "Back to view deal package"
            ])
            return

        # Detail screen
        print_header("Deal Detail Screen")
        print(f"\n  You are buying deal {deal.get_deal_id()} – \"{deal.get_name()}\".")
        print(f"\n  {deal.get_description()}")
        print(f"\n  Total fee             : ${deal.get_price():.2f}")
        print(f"  Your current fund     : ${user.get_fund_balance():.2f}")
        print(f"\n{DIVIDER}")
        choice = get_menu_choice([
            "Confirm payment",
            "Back to view deal package screen"
        ])
        if choice == 2:
            return

        # Process
        try:
            success, msg = self.__payment_processor.purchase_deal_package(user, deal)
        except InsufficientFundsException as e:
            print_header()
            print(f"\n  {e}")
            print(f"\n{DIVIDER}")
            get_menu_choice(["Back to view deal package"])
            return

        print_header("Payment Successful Screen")
        print("\n  Payment successful!")
        print("  Your deal package is now registered into your profile.")
        print("  To track your deal package usage, please go to")
        print("  \"View Profile Information\" menu.")
        print(f"\n{DIVIDER}")
        get_menu_choice([
            "Go to View Profile Information",
            "Back to view deal package"
        ])