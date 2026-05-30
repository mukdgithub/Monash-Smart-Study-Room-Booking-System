"""
MSSRB - Monash Smart Study Room Booking System
Entry point for the application.
"""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from boundary.auth_menu import AuthMenu
from boundary.main_menu import MainMenu
from controller.user_manager import UserManager


def main():
    """Application entry point."""
    user_manager = UserManager()
    auth_menu = AuthMenu(user_manager)
    main_menu = MainMenu()

    while True:
        user = auth_menu.show_welcome()
        if user:
            main_menu.show(user)
        else:
            print("\nExiting the system. Goodbye!")
            break


if __name__ == "__main__":
    main()