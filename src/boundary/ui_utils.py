"""
Shared UI display utilities for the MSSRB terminal interface.
"""

BANNER = "=" * 38
DIVIDER = "-" * 38
TITLE = "Study Room Booking System"


class ReturnToHomeException(Exception):
    """Raised from any screen when the user chooses 'Back to Main Menu'."""


def print_header(screen_title: str = ""):
    """Print the standard system header."""
    print(f"\n{BANNER}")
    print(TITLE)
    print(BANNER)
    print("_" * 38)
    if screen_title:
        print(f"\n{screen_title}")


def print_menu(options: list[str], prompt: str = None):
    """Print a numbered menu and return the prompt string."""
    print(f"\n{DIVIDER}")
    print("Menu:")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    nums = ", ".join(str(i) for i in range(1, len(options) + 1))
    if prompt is None:
        prompt = f"Enter your option ({nums}): "
    return prompt


def get_menu_choice(options: list[str], prompt: str = None,
                    show_home: bool = True) -> int:
    """
    Display a menu and loop until a valid integer choice is entered.
    Returns 1-based index (relative to the original options list).

    When show_home is True (default) a 'Back to Main Menu' item is
    appended automatically. If the user selects it, ReturnToHomeException
    is raised so the call stack unwinds all the way back to MainMenu.show().
    """
    HOME_LABEL = "Back to Main Menu"
    full_options = list(options)
    if show_home:
        full_options.append(HOME_LABEL)

    p = print_menu(full_options, prompt)
    valid = set(range(1, len(full_options) + 1))
    home_index = len(full_options) if show_home else None

    while True:
        raw = input(p).strip()
        if raw.isdigit() and int(raw) in valid:
            chosen = int(raw)
            if show_home and chosen == home_index:
                raise ReturnToHomeException()
            return chosen
        print_header("Invalid option screen")
        print("\nInvalid input.")
        print(f"Please enter digit 1, 2, ..., {len(full_options)} only.")
        print_menu(full_options, prompt)


def get_non_empty_input(prompt: str, field_name: str = "This field") -> str:
    """Prompt until non-empty input is provided."""
    while True:
        val = input(prompt).strip()
        if val:
            return val
        print(f"  {field_name} cannot be empty. Please try again.")


def pause(msg: str = "\nPress Enter to continue..."):
    input(msg)