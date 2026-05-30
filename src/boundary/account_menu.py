"""
Boundary class for Account Management screens.
"""

from boundary.ui_utils import print_header, get_menu_choice, DIVIDER, pause
from controller.user_manager import UserManager
from controller.user_deal_manager import UserDealManager
from controller.deal_package_manager import DealPackageManager
from entity.user import User


class AccountMenu:
    """Handles account management including profile, fund top-up, and history."""

    def __init__(self, user_manager: UserManager,
                 user_deal_manager: UserDealManager,
                 deal_package_manager: DealPackageManager):
        self.__user_manager         = user_manager
        self.__user_deal_manager    = user_deal_manager
        self.__deal_package_manager = deal_package_manager

    def show(self, user: User):
        """Display the Account Management menu."""
        while True:
            print_header("Manage Account Screen")
            print("\nAccount Management.")
            print("Manage your account with the menu below.")
            if not user.is_admin():
                choice = get_menu_choice([
                    "View profile information",
                    "View account status",
                    "Manage Fund"
                ])
                if choice == 1:
                    self.__show_profile(user)
                elif choice == 2:
                    self.__show_usage_status(user)
                elif choice == 3:
                    self.__manage_fund(user)
            else:
                choice = get_menu_choice(["View profile information"])
                if choice == 1:
                    self.__show_profile(user)

    # ------------------------------------------------------------------ #
    #  Profile                                                              #
    # ------------------------------------------------------------------ #

    def __show_profile(self, user: User):
        print_header("View Profile Information Screen")
        print(f"\n  Username    : {user.get_first_name()} {user.get_last_name()}")
        print(f"  User ID     : {user.get_user_id()}")
        print(f"  Role        : {user.get_role().capitalize()}")
        print(f"  Email       : {user.get_email()}")
        if user.is_student():
            print(f"  Student ID  : {user.get_student_id()}")
            print(f"  Phone       : {user.get_phone()}")
            print(f"  Fund balance: ${user.get_fund_balance():.2f}")
        if user.is_admin():
            print(f"  Phone       : {user.get_phone()}")

        active_deals = self.__user_deal_manager.get_active_deals_for_user(
            user.get_user_id()
        )
        if active_deals or not user.is_admin():
            print(f"  Deal package(s):")
            for ud in active_deals:
                pkg = self.__deal_package_manager.find_deal_by_id(
                    ud.get_deal_package_id()
                )
                pkg_name = pkg.get_name() if pkg else ud.get_deal_package_id()
                print(f"    [{ud.get_deal_instance_id()}] {pkg_name} "
                      f"| {ud.get_hours_remaining():.1f} hrs remaining "
                      f"| Purchased: {ud.get_purchased_at()}")
        else:
            if not user.is_admin():
                print("  Deal package: None")

        print(f"\n{DIVIDER}")
        get_menu_choice(["Back to Manage Account"])

    # ------------------------------------------------------------------ #
    #  Usage status                                                         #
    # ------------------------------------------------------------------ #

    def __show_usage_status(self, user: User):
        print_header("View Usage Status Screen")
        suspended = user.get_is_suspended()
        print(f"\n  Strikes     : {user.get_strike_count()} / 3")
        if suspended:
            print(f"  Status      : SUSPENDED until {user.get_suspension_end()}")
        else:
            print("  Status      : Active")

        active_deals = self.__user_deal_manager.get_active_deals_for_user(
            user.get_user_id()
        )
        if active_deals:
            print(f"  Deal package(s):")
            for ud in active_deals:
                pkg = self.__deal_package_manager.find_deal_by_id(
                    ud.get_deal_package_id()
                )
                pkg_name = pkg.get_name() if pkg else ud.get_deal_package_id()
                print(f"    [{ud.get_deal_instance_id()}] {pkg_name} "
                      f"| {ud.get_hours_remaining():.1f} hrs remaining")
        else:
            print("  Deal package  : None")

        print(f"\n{DIVIDER}")
        get_menu_choice(["Back to Manage Account"])

    # ------------------------------------------------------------------ #
    #  Fund management                                                      #
    # ------------------------------------------------------------------ #

    def __manage_fund(self, user: User):
        while True:
            print_header("Manage Fund Screen")
            print(f"\n  Your current balance: ${user.get_fund_balance():.2f}")
            choice = get_menu_choice([
                "Add fund",
                "View Transaction Record",
                "Back to Account Management"
            ])
            if choice == 1:
                self.add_fund(user)
            elif choice == 2:
                self.__view_transactions(user)
            elif choice == 3:
                return

    def add_fund(self, user: User):
        while True:
            print_header("Add Fund Screen")
            print(f"\n  Add funds.")
            print(f"  Your current balance: ${user.get_fund_balance():.2f}")
            raw = input("  Enter amount to add: $").strip()
            try:
                amount = float(raw)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                print_header("Add Fund Screen")
                print("\n  Add funds.")
                print("  You entered invalid amount.")
                print("  Please re-enter.")
                continue

            print_header("Confirm Add Fund Screen")
            print(f"\n  You are adding ${amount:.2f} to your balance.")
            print(f"\n{DIVIDER}")
            choice = get_menu_choice([
                "Approve the amount",
                "Edit the amount",
                "Cancel and back to Manage Fund"
            ])
            if choice == 1:
                self.__user_manager.top_up_fund(user, amount)
                print_header("Successful Fund Addition Screen")
                print(f"\n  ${amount:.2f} has been added into your fund.")
                print(f"  Your current balance is: ${user.get_fund_balance():.2f}")
                print(f"\n{DIVIDER}")
                get_menu_choice(["Back to Manage Fund"])
                return
            elif choice == 2:
                continue
            elif choice == 3:
                return

    def __view_transactions(self, user: User):
        print_header("View Transaction Record Screen")
        transactions = self.__user_manager.get_transactions(user.get_user_id())
        if not transactions:
            print("\n  No transaction records found.")
        else:
            print()
            for t in transactions:
                print(f"  [{t.get_transaction_type()}] ${t.get_amount():.2f} | "
                      f"{t.get_description()} | {t.get_timestamp()}")
        print(f"\n{DIVIDER}")
        get_menu_choice(["Go back to Manage Fund"])