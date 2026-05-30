"""
Entity class representing a system user (Student or Admin).
"""


class User:
    """Represents a registered user of the MSSRB system."""

    def __init__(self, user_id: str, first_name: str, last_name: str,
                 email: str, phone: str, password: str, role: str,
                 fund_balance: float = 0.0, is_suspended: bool = False,
                 newbie_used: bool = False, strike_count: int = 0,
                 suspension_end: str = "", student_id: str = ""):
        """
        Initialise a User instance.

        Args:
            user_id (str): Unique identifier for the user.
            first_name (str): User's first name.
            last_name (str): User's last name.
            email (str): User's email address.
            phone (str): User's contact phone number.
            password (str): User's plain-text password.
            role (str): Either "student" or "admin".
            fund_balance (float): Current fund balance; defaults to 0.0.
            is_suspended (bool): Whether the account is currently suspended.
            newbie_used (bool): Whether the one-time newbie discount has been used.
            strike_count (int): Number of policy strikes accumulated.
            suspension_end (str): Date the suspension lifts in dd/mm/yyyy format, or "" if not suspended.
            student_id (str): University student ID; empty string for admin accounts.

        Returns:
            None
        """
        self.__user_id        = user_id
        self.__first_name     = first_name
        self.__last_name      = last_name
        self.__email          = email
        self.__phone          = phone
        self.__password       = password
        self.__role           = role  # "student" or "admin"
        self.__fund_balance   = float(fund_balance)   # coerce CSV string to float on load
        self.__is_suspended   = is_suspended
        self.__newbie_used    = newbie_used
        self.__strike_count   = int(strike_count)     # coerce CSV string to int on load
        self.__suspension_end = suspension_end  # dd/mm/yyyy or ""
        self.__student_id     = student_id      # populated for students, "" for admins

    # --- Getters ---
    def get_user_id(self) -> str:
        """Return the unique user ID."""
        return self.__user_id

    def get_first_name(self) -> str:
        """Return the user's first name."""
        return self.__first_name

    def get_last_name(self) -> str:
        """Return the user's last name."""
        return self.__last_name

    def get_email(self) -> str:
        """Return the user's email address."""
        return self.__email

    def get_phone(self) -> str:
        """Return the user's contact phone number."""
        return self.__phone

    def get_password(self) -> str:
        """Return the user's password."""
        return self.__password

    def get_role(self) -> str:
        """Return the user's role ('student' or 'admin')."""
        return self.__role

    def get_fund_balance(self) -> float:
        """Return the user's current fund balance."""
        return self.__fund_balance

    def get_is_suspended(self) -> bool:
        """Return True if the user account is currently suspended."""
        return self.__is_suspended

    def get_newbie_used(self) -> bool:
        """Return True if the one-time newbie discount has already been applied."""
        return self.__newbie_used

    def get_strike_count(self) -> int:
        """Return the number of policy strikes accumulated by the user."""
        return self.__strike_count

    def get_suspension_end(self) -> str:
        """Return the suspension end date as a dd/mm/yyyy string, or '' if not suspended."""
        return self.__suspension_end

    def get_student_id(self) -> str:
        """Return the university student ID, or '' for admin accounts."""
        return self.__student_id

    # --- Setters ---
    def set_fund_balance(self, amount: float):
        """
        Update the user's fund balance.

        Args:
            amount (float): New balance value to assign.

        Returns:
            None
        """
        self.__fund_balance = float(amount)

    def set_is_suspended(self, val: bool):
        """
        Set the suspension status of the user account.

        Args:
            val (bool): True to suspend, False to reinstate.

        Returns:
            None
        """
        self.__is_suspended = val

    def set_newbie_used(self, val: bool):
        """
        Mark whether the one-time newbie discount has been used.

        Args:
            val (bool): True if the discount has been consumed.

        Returns:
            None
        """
        self.__newbie_used = val

    def set_strike_count(self, val: int):
        """
        Update the user's strike count.

        Args:
            val (int): New strike count value.

        Returns:
            None
        """
        self.__strike_count = int(val)

    def set_suspension_end(self, val: str):
        """
        Set the date on which the current suspension lifts.

        Args:
            val (str): Date string in dd/mm/yyyy format, or '' to clear.

        Returns:
            None
        """
        self.__suspension_end = val

    def set_phone(self, val: str):
        """
        Update the user's contact phone number.

        Args:
            val (str): New phone number string.

        Returns:
            None
        """
        self.__phone = val

    def set_student_id(self, val: str):
        """
        Set the university student ID for this user.

        Args:
            val (str): Student ID string; pass '' to clear.

        Returns:
            None
        """
        self.__student_id = val

    def is_admin(self) -> bool:
        """
        Check whether the user holds the admin role.

        Returns:
            bool: True if the user's role is 'admin' (case-insensitive).
        """
        return self.__role.lower() == "admin"

    def is_student(self) -> bool:
        """
        Check whether the user holds the student role.

        Returns:
            bool: True if the user's role is 'student' (case-insensitive).
        """
        return self.__role.lower() == "student"

    def to_csv_row(self) -> list:
        """
        Serialise the user to a flat list suitable for writing as a CSV row.

        Returns:
            list: Ordered list of string values matching the CSV column layout:
                  [user_id, first_name, last_name, email, phone, password, role,
                   fund_balance, is_suspended, newbie_used, strike_count,
                   suspension_end, student_id]
        """
        return [
            self.__user_id, self.__first_name, self.__last_name,
            self.__email, self.__phone, self.__password, self.__role,
            str(self.__fund_balance), str(self.__is_suspended),
            str(self.__newbie_used), str(self.__strike_count),
            self.__suspension_end, self.__student_id
        ]

    def __str__(self):
        """
        Return a human-readable summary of the user.

        Returns:
            str: Formatted string showing role, full name, and email.
        """
        return (f"[{self.__role.upper()}] {self.__first_name} {self.__last_name} "
                f"<{self.__email}>")
