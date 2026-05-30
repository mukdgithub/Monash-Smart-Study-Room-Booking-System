"""
Boundary class for authentication screens (welcome, register, login).
"""

import re

from boundary.ui_utils import print_header, get_menu_choice, pause
from controller.user_manager import UserManager
from entity.user import User

# Accepted Monash email domains
_MONASH_EMAIL_RE = re.compile(
    r'^[a-zA-Z0-9._%+\-]+@(student\.monash\.edu|monash\.edu)$',
    re.IGNORECASE
)


class AuthMenu:
    """Handles the Welcome, Register, and Login screens."""

    MAX_LOGIN_ATTEMPTS = 5

    def __init__(self, user_manager: UserManager):
        self.__user_manager = user_manager

    def show_welcome(self) -> User | None:
        """
        Display the welcome screen and direct to register or login.
        Returns the authenticated User or None if the user exits.
        """
        while True:
            print_header("Welcome Screen")
            print("\nWelcome to the Monash Smart Study Room Booking System.")
            print("Book, manage and explore study rooms with ease.\n")
            choice = get_menu_choice(["Register an account.", "Sign in.", "Exit"], show_home=False)
            if choice == 1:
                self.__register_flow()
            elif choice == 2:
                user = self.__login_flow()
                if user:
                    return user
            elif choice == 3:
                break

    # ------------------------------------------------------------------ #
    #  Registration                                                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def __prompt_non_empty(label: str) -> str:
        """Re-prompt until the user enters a non-empty value."""
        while True:
            value = input(f"  {label}: ").strip()
            if value:
                return value
            print(f"  {label} cannot be empty. Please try again.")

    @staticmethod
    def __prompt_valid_email() -> str:
        """Re-prompt until the user enters a valid Monash email address."""
        while True:
            email = input("  Email: ").strip()
            if not email:
                print("  Email cannot be empty. Please try again.")
            elif not _MONASH_EMAIL_RE.match(email):
                print("  Invalid email. Only @student.monash.edu or @monash.edu addresses are accepted.")
            else:
                return email

    @staticmethod
    def __prompt_valid_phone() -> str:
        """Re-prompt until the user enters a valid phone number (digits only, ≥ 8)."""
        while True:
            phone = input("  Phone number (digits only, min 8): ").strip()
            if not phone.isdigit():
                print("  Phone number must contain digits only. Please try again.")
            elif len(phone) < 8:
                print("  Phone number must be at least 8 digits. Please try again.")
            else:
                return phone

    @staticmethod
    def __prompt_valid_student_id() -> str:
        """Re-prompt until the user enters a non-empty student ID."""
        while True:
            sid = input("  Student ID: ").strip()
            if sid:
                return sid
            print("  Student ID cannot be empty. Please try again.")

    @staticmethod
    def __prompt_valid_password() -> str:
        """Re-prompt until the user enters a password ≥ 6 chars and confirms it."""
        while True:
            password = input("  Password (min 6 characters): ").strip()
            if len(password) < 6:
                print("  Password must be at least 6 characters. Please try again.")
                continue
            confirm = input("  Confirm password: ").strip()
            if password != confirm:
                print("  Passwords do not match. Please try again.")
                continue
            return password

    @staticmethod
    def __role_from_email(email: str) -> str:
        """Derive role from a validated Monash email address."""
        return "student" if email.lower().endswith("@student.monash.edu") else "admin"

    def __register_flow(self):
        """
        Display the registration form and handle submission.

        Role is determined automatically from the email domain:
          @student.monash.edu  →  student  (requires first name, last name,
                                            student ID, email, password)
          @monash.edu          →  admin    (requires first name, last name,
                                            phone number, email, password)

        Each field is validated inline with a clear per-field error and re-prompt
        so users are never sent back to the welcome screen for a correctable mistake.
        """
        print_header("Account Registration Screen")
        print("\nRegister your account.")
        print("  Enter your Monash email first — the form will adapt to your role.")
        print("  (All fields are required)\n")

        # Collect email first so we can determine role and show the correct form
        email = self.__prompt_valid_email()
        role  = self.__role_from_email(email)

        if role == "student":
            print_header("Student Account Registration Screen")
            print("\n  Registering as: Student\n")
            first_name  = self.__prompt_non_empty("First Name")
            last_name   = self.__prompt_non_empty("Last Name")
            student_id  = self.__prompt_valid_student_id()
            phone       = self.__prompt_valid_phone()
            password    = self.__prompt_valid_password()
        else:
            print_header("Admin Account Registration Screen")
            print("\n  Registering as: Admin\n")
            first_name  = self.__prompt_non_empty("First Name")
            last_name   = self.__prompt_non_empty("Last Name")
            phone       = self.__prompt_valid_phone()
            student_id  = ""          # not collected for admins
            password    = self.__prompt_valid_password()

        success, result = self.__user_manager.register_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            password=password,
            student_id=student_id,
        )

        if success:
            print_header("Account Registration Successful Screen")
            print("\n  Account Registration Successful.")
            role_label = "Student" if role == "student" else "Admin"
            print(f"  Welcome, {first_name}! Your {role_label} account is ready.")
            print(f"  You can now sign in.")
            print(f"\n{'-'*32}")
            get_menu_choice(["Back to Welcome Screen"], show_home=False)
        else:
            print_header("Account Registration Unsuccessful Screen")
            print("\n  Account Registration Unsuccessful.")
            if "already registered" in result and "email" in result.lower():
                print("  That email address already has an account.")
            elif "Student ID is already registered" in result:
                print("  That Student ID is already linked to an existing account.")
            elif "phone number is already registered" in result:
                print("  That phone number is already linked to an existing account.")
            else:
                print(f"  {result}")
            print(f"\n{'-'*32}")
            get_menu_choice(["Back to Welcome Screen"], show_home=False)

    # ------------------------------------------------------------------ #
    #  Login                                                                #
    # ------------------------------------------------------------------ #

    def __login_flow(self) -> User | None:
        """
        Display the login screen. Allows up to MAX_LOGIN_ATTEMPTS.
        Returns the authenticated User on success, None otherwise.
        """
        attempts = 0

        while attempts < self.MAX_LOGIN_ATTEMPTS:
            if attempts == 0:
                print_header("Sign in Screen")
            else:
                print_header("Re-attempt Sign in Screen")
                print("\n  Invalid credentials. Please try again.")
                print(f"  Attempts remaining: {self.MAX_LOGIN_ATTEMPTS - attempts}")

            print("\n  Enter your email and password:")
            email    = input("  Email: ").strip()
            password = input("  Password: ").strip()

            user = self.__user_manager.authenticate(email, password)
            if user:
                return user

            attempts += 1

        # Exceeded max attempts
        print_header("Invalid Sign-in Credential Screen")
        print("\n  Too many failed attempts.")
        print("  Please contact system admin.")
        pause()
        return None