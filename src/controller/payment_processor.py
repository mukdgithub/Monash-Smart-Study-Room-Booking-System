"""
Controller class responsible for payment processing, refunds, and deal package purchases.
"""

from entity.user import User
from entity.booking import Booking
from entity.deal_package import DealPackage
from entity.user_deal import UserDeal
from controller.user_manager import UserManager
from controller.user_deal_manager import UserDealManager


class InsufficientFundsException(Exception):
    """Raised when a student does not have enough funds for a transaction."""
    pass


class PaymentProcessor:
    """
    Handles all payment-related operations.
    No fund deductions occur anywhere except through this class.
    """

    NEWBIE_CODE = "NEWBIE20"

    def __init__(self, user_manager: UserManager, user_deal_manager: UserDealManager):
        """
        Initialise PaymentProcessor with its dependent managers.

        Args:
            user_manager (UserManager): Handles fund deductions, credits, and transaction logging.
            user_deal_manager (UserDealManager): Handles deal hour consumption and restoration.

        Returns:
            None
        """
        self.__user_manager      = user_manager
        self.__user_deal_manager = user_deal_manager

    def execute_payment(self, user: User, booking: Booking,
                        user_deal: UserDeal = None) -> bool:
        """
        Deduct the booking fee from the student's fund.
        If a UserDeal is provided and has sufficient hours, the booking is
        paid entirely via the deal (single payment method — no partial coverage).
        Raises InsufficientFundsException if funds are insufficient.
        Returns True on success.
        """
        total_fee    = booking.get_total_fee()
        hours_needed = booking.get_duration_hours()

        if user_deal:
            if user_deal.get_hours_remaining() >= hours_needed:
                # Fully covered by deal — consume hours, no fund deduction
                self.__user_deal_manager.consume_hours(user_deal, hours_needed)  # hours_needed retrieved from Booking entity
                self.__user_manager.deduct_fund(
                    user, 0.0,  # $0 deduction still logs a transaction entry for the deal payment
                    f"Booking {booking.get_booking_id()} paid via deal "
                    f"{user_deal.get_deal_instance_id()}"
                )
                return True
            # Deal has insufficient hours — fall through to standard fund payment
            # (single payment method: do not mix deal hours with fund balance)

        # Standard fund payment
        if user.get_fund_balance() < total_fee:
            raise InsufficientFundsException(
                f"Insufficient funds. Required: ${total_fee:.2f}, "
                f"Available: ${user.get_fund_balance():.2f}"
            )
        return self.__user_manager.deduct_fund(
            user, total_fee,
            f"Payment for booking {booking.get_booking_id()}"  # booking ID retrieved from Booking entity to label the transaction
        )

    def execute_refund(self, user: User, booking: Booking,
                       refund_percent: float,
                       user_deal: UserDeal = None) -> bool:
        """
        Reverse the payment for a cancelled booking.

        - If the booking was paid via a UserDeal (deal_instance_id is set on
          the booking), restore the deal hours instead of crediting the fund.
        - The equipment deposit is always a fund charge, so it is always
          refunded to the fund regardless of payment method.
        - Returns False if refund_amount <= 0.
        """
        if refund_percent <= 0:
            if booking.has_equipment():
                deposit = Booking.EQUIPMENT_DEPOSIT
                if deposit > 0:
                    self.__user_manager.credit_fund(
                        user, deposit,
                        f"Equipment deposit refund for booking {booking.get_booking_id()}"
                    )
            return False

        if booking.was_paid_by_deal() and user_deal:
            # Restore deal hours for the room fee portion
            hours_to_restore = booking.get_duration_hours() * refund_percent  # proportional to how much of the booking is being refunded
            self.__user_deal_manager.restore_hours(user_deal, hours_to_restore)  # credits hours back to the deal instead of money to the fund

            # Equipment deposit is always charged to fund — refund it separately
            deposit = Booking.EQUIPMENT_DEPOSIT if booking.has_equipment() else 0.0
            if deposit > 0:
                self.__user_manager.credit_fund(
                    user, deposit,
                    f"Equipment deposit refund for booking {booking.get_booking_id()}"
                )
        else:
            # Standard fund payment — refund room-fee portion at given percent,
            # plus equipment deposit IN FULL (if any).
            deposit = Booking.EQUIPMENT_DEPOSIT if booking.has_equipment() else 0.0
            room_fee = booking.get_total_fee() - deposit
            refund = room_fee * refund_percent + deposit
            self.__user_manager.credit_fund(
                user, refund,
                f"Refund for cancelled booking {booking.get_booking_id()}"
            )
        return True

    def execute_no_show_penalty(self, user: User, booking: Booking,
                                room) -> tuple[float, str]:
        """
        Apply no-show penalty based on room type.

        Refund rules:
          Small  → 20% of room fee refunded (80% forfeited).
                   Equipment deposit always fully refunded.
          Medium → 0%  of room fee refunded (100% forfeited).
                   Equipment deposit always fully refunded.
          Large  → 0%  of room fee refunded (100% forfeited).
                   Equipment deposit always fully refunded.

        Returns (refund_amount, note).
        """
        total_fee = booking.get_total_fee()
        room_type = room.get_room_type()

        deposit  = Booking.EQUIPMENT_DEPOSIT if booking.has_equipment() else 0.0
        room_fee = total_fee - deposit

        if room_type == "small":
            room_refund = room_fee * 0.2
            note        = "No-show: 80% of room fee forfeited, 20% refunded."
        else:
            room_refund = 0.0
            note        = "No-show: full room fee forfeited."

        # Deposit always fully returned regardless of room type
        total_refund = room_refund + deposit
        if deposit > 0:
            note += f" Equipment deposit of ${deposit:.2f} fully refunded."

        deal = self.__user_deal_manager.find_instance_by_id(booking.get_deal_instance_id())  # deal instance ID is stored on the Booking entity at payment time

        try:
            hours = booking.get_duration_hours() * room_refund / room_fee  # scales refunded hours proportionally to the refunded room fee
        except ZeroDivisionError:
            hours = 0  # room_fee can be 0 if the booking was free (e.g. newbie promo)

        if booking.was_paid_by_deal():
            self.__user_deal_manager.restore_hours(deal, hours)
            self.__user_manager.credit_fund(
                        user, deposit,
                        f"Equipment deposit refund for booking {booking.get_booking_id()}"
                    )
        else:
            self.__user_manager.credit_fund(
                user, total_refund,
                f"No-show partial refund for booking {booking.get_booking_id()}"
            )
        return total_refund, note

    def apply_newbie_promo(self, user: User, room_type: str) -> tuple[bool, str]:
        """
        Validate and apply the NEWBIE20 promo code.
        Returns (eligible, message).
        """
        if user.get_newbie_used():
            return False, "Your NEWBIE promo code has already been used."
        if room_type.lower() != "small":
            return False, "The NEWBIE promo code is only applicable to small room bookings."
        return True, "NEWBIE20 promo code applied! Your booking fee will be $0."

    def purchase_deal_package(self, user: User,
                               deal: DealPackage) -> tuple[bool, str]:
        """
        Purchase a deal package by deducting its price from the user's fund.
        Creates a new UserDeal instance on success.
        Raises InsufficientFundsException if insufficient funds.
        Returns (success, message).
        """
        if user.get_fund_balance() < deal.get_price():
            raise InsufficientFundsException(
                f"Insufficient funds. Required: ${deal.get_price():.2f}, "
                f"Available: ${user.get_fund_balance():.2f}"
            )
        success = self.__user_manager.deduct_fund(
            user, deal.get_price(),
            f"Purchase of deal package: {deal.get_name()}"
        )
        if success:
            self.__user_deal_manager.create_deal_instance(user.get_user_id(), deal)  # creates the UserDeal record linked to this user and package
        return success, f"Deal package '{deal.get_name()}' purchased successfully!"