"""
Controller class responsible for user registration, login, and account management.
"""

import csv
import os
import re
import uuid
from datetime import datetime

from entity.user import User
from entity.transaction import Transaction

# Accepted Monash email pattern — anchored so nothing like "foo@monash.edu.evil.com" passes
_MONASH_EMAIL_RE = re.compile(
    r'^[a-zA-Z0-9._%+\-]+@(student\.monash\.edu|monash\.edu)$',
    re.IGNORECASE
)


class UserManager:
    """Manages user registration, authentication, and profile operations."""

    USERS_FILE        = os.path.join(os.path.dirname(__file__), "../data/users.csv")
    TRANSACTIONS_FILE = os.path.join(os.path.dirname(__file__), "../data/transactions.csv")

    HEADERS = [
        "user_id", "first_name", "last_name", "email", "phone",
        "password", "role", "fund_balance", "is_suspended",
        "newbie_used", "strike_count", "suspension_end", "student_id"
    ]

    def __init__(self):
        """
        Initialise UserManager and load all users from CSV into memory.

        Returns:
            None
        """
        self.__users: list[User] = []
        self.__load_users()

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def __load_users(self):
        """Load users from CSV into memory."""
        self.__users = []
        path = os.path.abspath(self.USERS_FILE)
        if not os.path.exists(path):
            return
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                user = User(
                    user_id=row["user_id"],
                    first_name=row["first_name"],
                    last_name=row["last_name"],
                    email=row["email"],
                    phone=row["phone"],
                    password=row["password"],
                    role=row["role"],
                    fund_balance=float(row.get("fund_balance", 0)),
                    is_suspended=row.get("is_suspended", "False") == "True",  # CSV stores booleans as strings
                    newbie_used=row.get("newbie_used", "False") == "True",    # same string-to-bool pattern
                    strike_count=int(row.get("strike_count") or 0),           # `or 0` guards against None when column is missing
                    suspension_end=row.get("suspension_end", ""),
                    student_id=row.get("student_id", "")
                )
                self.__users.append(user)

    def __save_users(self):
        """Persist all users back to CSV."""
        path = os.path.abspath(self.USERS_FILE)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADERS)
            for u in self.__users:
                writer.writerow(u.to_csv_row())

    def __generate_user_id(self) -> str:
        """
        Generate a unique user ID prefixed with 'U'.

        Returns:
            str: A new user ID in the format 'U' + 8 uppercase hex characters.
        """
        return "U" + str(uuid.uuid4())[:8].upper()

    # ------------------------------------------------------------------ #
    #  Public methods                                                        #
    # ------------------------------------------------------------------ #

    def register_user(self, first_name: str, last_name: str, email: str,
                      phone: str = "", password: str = "",
                      student_id: str = "") -> tuple[bool, str]:
        """
        Register a new user.

        Role is derived from the email domain:
          @student.monash.edu  →  student  (student_id required, phone not used)
          @monash.edu          →  admin    (phone required, student_id not used)

        Returns (success: bool, message: str).
        """
        # --- common field validation ---
        if not first_name.strip() or not last_name.strip():
            return False, "First name and last name cannot be empty."
        if not email.strip() or not _MONASH_EMAIL_RE.match(email.strip()):
            return False, "Please enter a valid Monash email address (@student.monash.edu or @monash.edu)."
        if len(password) < 6:
            return False, "Password must be at least 6 characters."
        if self.find_user_by_email(email):
            return False, "This email address is already registered."

        # --- derive role from email domain ---
        normalised_email = email.strip().lower()
        if normalised_email.endswith("@student.monash.edu"):
            role = "student"
        else:
            role = "admin"

        # --- role-specific field validation and duplicate checks ---
        if role == "student":
            if not student_id.strip():
                return False, "Student ID cannot be empty."
            if self.find_user_by_student_id(student_id):
                return False, "This Student ID is already registered."
            if not phone.strip().isdigit() or len(phone.strip()) < 8:
                return False, "Phone number must be at least 8 digits."
            if self.find_user_by_phone(phone):
                return False, "This phone number is already registered."
            resolved_phone = phone.strip()
        else:
            if not phone.strip().isdigit() or len(phone.strip()) < 8:
                return False, "Phone number must be at least 8 digits."
            if self.find_user_by_phone(phone):
                return False, "This phone number is already registered."
            resolved_phone = phone.strip()

        user_id  = self.__generate_user_id()
        new_user = User(
            user_id=user_id,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            email=normalised_email,
            phone=resolved_phone,
            password=password,
            role=role,
            student_id=student_id.strip() if role == "student" else ""
        )
        self.__users.append(new_user)
        self.__save_users()
        return True, user_id

    def authenticate(self, email: str, password: str) -> User | None:
        """
        Authenticate a user. Returns the User object on success, None otherwise.
        """
        user = self.find_user_by_email(email.strip().lower())
        if user and user.get_password() == password:
            return user
        return None

    def find_user_by_email(self, email: str) -> User | None:
        """Find a user by email address (case-insensitive)."""
        for u in self.__users:
            if u.get_email().lower() == email.lower():
                return u
        return None

    def find_user_by_id(self, user_id: str) -> User | None:
        """Find a user by their user ID."""
        for u in self.__users:
            if u.get_user_id() == user_id:
                return u
        return None

    def find_user_by_phone(self, phone: str) -> User | None:
        """Find any user by phone number. Returns None if not found."""
        for u in self.__users:
            if u.get_phone() and u.get_phone() == phone.strip():
                return u
        return None

    def find_user_by_student_id(self, student_id: str) -> User | None:
        """Find a student by student ID. Returns None if not found."""
        for u in self.__users:
            if u.get_student_id() and u.get_student_id() == student_id.strip():
                return u
        return None

    def top_up_fund(self, user: User, amount: float) -> tuple[bool, str]:
        """
        Add funds to a student's account.
        Returns (success, message).
        """
        if amount <= 0:
            return False, "Top-up amount must be greater than zero."
        user.set_fund_balance(user.get_fund_balance() + amount)
        self.save_user(user)
        self.__record_transaction(
            user.get_user_id(), Transaction.TYPE_CREDIT, amount,  # TYPE_CREDIT is a class constant on Transaction
            f"Fund top-up of ${amount:.2f}"
        )
        return True, f"${amount:.2f} has been added to your fund."

    def deduct_fund(self, user: User, amount: float, description: str) -> bool:
        """Deduct funds from user. Returns False if insufficient."""
        if user.get_fund_balance() < amount:
            return False
        user.set_fund_balance(user.get_fund_balance() - amount)
        self.save_user(user)
        self.__record_transaction(user.get_user_id(), Transaction.TYPE_DEBIT, amount, description)  # TYPE_DEBIT is a class constant on Transaction
        return True

    def credit_fund(self, user: User, amount: float, description: str):
        """Credit funds back to user (refund)."""
        user.set_fund_balance(user.get_fund_balance() + amount)
        self.save_user(user)
        self.__record_transaction(user.get_user_id(), Transaction.TYPE_REFUND, amount, description)  # TYPE_REFUND is a class constant on Transaction

    def get_transactions(self, user_id: str) -> list[Transaction]:
        """Load and return all transactions for a given user."""
        transactions = []
        path = os.path.abspath(self.TRANSACTIONS_FILE)
        if not os.path.exists(path):
            return transactions
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["user_id"] == user_id:
                    transactions.append(Transaction(
                        transaction_id=row["transaction_id"],
                        user_id=row["user_id"],
                        transaction_type=row["transaction_type"],
                        amount=float(row["amount"]),
                        description=row["description"],
                        timestamp=row["timestamp"]
                    ))
        return transactions

    def add_strike(self, user: User) -> bool:
        """
        Add a strike to a student. Suspends for 3 months at 3 strikes.
        Returns True if suspended now.
        """
        user.set_strike_count(user.get_strike_count() + 1)
        if user.get_strike_count() >= 3:
            from datetime import date
            from dateutil.relativedelta import relativedelta
            end = date.today() + relativedelta(months=3)  # relativedelta gives a calendar-accurate 3-month offset
            user.set_suspension_end(end.strftime("%d/%m/%Y"))  # format must match the system's dd/mm/yyyy convention
            user.set_is_suspended(True)
            self.save_user(user)
            return True
        self.save_user(user)
        return False

    def save_user(self, user: User):
        """Persist a single user's updated state."""
        for u in self.__users:
            if u.get_user_id() == user.get_user_id():
                u.set_fund_balance(user.get_fund_balance())
                u.set_strike_count(user.get_strike_count())
                u.set_suspension_end(user.get_suspension_end())
                u.set_is_suspended(user.get_is_suspended())
                u.set_newbie_used(user.get_newbie_used())
                u.set_phone(user.get_phone())
                u.set_student_id(user.get_student_id())
        self.__save_users()

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def __record_transaction(self, user_id: str, t_type: str,
                             amount: float, description: str):
        """Append a transaction record to the CSV."""
        path      = os.path.abspath(self.TRANSACTIONS_FILE)
        tx_id     = "T" + str(uuid.uuid4())[:8].upper()
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        row       = [tx_id, user_id, t_type, str(amount), description, timestamp]
        file_exists = os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["transaction_id", "user_id", "transaction_type",
                                 "amount", "description", "timestamp"])
            writer.writerow(row)