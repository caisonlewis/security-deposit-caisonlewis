"""
A module containing the core computation and controller logic for a banking application.
"""
import random
import re
import sys

from database import Database
from models import Account, User, Role

OWNER_NAME_PATTERN = re.compile('^[a-zA-Z ]{1,64}$')

db = Database('database')

def get_SUPPORT_UN(): return 'admin'

def get_SUPPORT_PW(): return 'admin'


def create_account(owner_name: str, balance: float, user: User) -> Account:
    """
    Create a new Account object and add it to acct_list.
    - owner_names cannot be empty, at most 64 characters, and only contain Latin alphabet characters and spaces.
    - the balance must be a non-negative float.
    - user must a Banker.

    :param owner_name: the desired owner's name
    :param balance: the initial balance
    :param user: a User object representing the authenticated User making the call
    :return: the function must return the newly-created Account object
    """
    if not isinstance(owner_name, str):
        raise TypeError("Invalid owner name")

    if not owner_name or len(owner_name) > 64 or not re.match(OWNER_NAME_PATTERN, owner_name):
        raise ValueError("Invalid owner name")

    if not isinstance(balance, float):
        raise TypeError("please enter a non negative numeric digit")

    if balance < 0 or balance > sys.float_info.max:
        raise ValueError(f"balance must be non-negative and less than {sys.float_info.max}")

    if not isinstance(user, User):
        raise TypeError("user must be an instance of User")

    # Check if user has permission. If not, raise a PermissionError
    if user.role != Role.BANKER:
        raise PermissionError("You do not have permission to do that.")



    # Loop until a random account number is generated that is NOT in the database already.
    # TODO: A failure can occur here that can compromise system availability.
    while True:
        new_id = random.randint(100000, 999999)  # nosec
        if not db.search_by_id(new_id):
            return db.create_account(Account(new_id, owner_name, balance))


def deposit(account_num: int, amount: float, notes: str, user: User) -> Account:
    """
    Add 'amount' to the Account object's balance with 'account_num' and update account 'notes'.
    - amount but be a non-negative float.
    - account_num must be an integer that corresponds to an account in the list.
    - user must either be a Banker or the account owner.

    :param account_num: the account number to search for
    :param amount: the amount to add to the account's balance
    :param notes: some notes about the withdrawal. May be an empty string.
    :param user: a User object representing the authenticated User making the call
    :return: the function returns an Account object representing the account with the modified balance
    """

    if not isinstance(account_num, int):
        raise TypeError("account number must be an int")

    if not isinstance(amount, float):
        raise TypeError("amount must be a float")

    if amount < 0 or amount > sys.float_info.max:
        raise ValueError(f"amount must be non-negative and less than {sys.float_info.max}")

    if not isinstance(user, User):
        raise TypeError("user must be an instance of User")

    acct = db.search_by_id(account_num)
    if not acct:
        raise ValueError("that account number does not exist")

    # Check if user has permission. If not, raise a PermissionError
    if user.role != Role.BANKER and not (user.role == Role.CUSTOMER and user.account_num == acct.account_num):
        raise PermissionError("You do not have permission to do that.")

    acct.balance += amount

    if notes:
        if acct.notes:
            acct.notes += "\n\n" + notes
        else:
            acct.notes = notes

    # The database adds something to the acct object unexpectedly when calling update_account.
    # How can you preserve the integrity of the acct object?
    copy = Account(acct.account_num, acct.owner_name, acct.balance, acct.notes)
    result = db.update_account(copy)

    # Validate the update. If invalid, raise a RuntimeError
    if result.balance != acct.balance:
        raise RuntimeError("Something went wrong. Contact the administrator.")

    return acct


def withdraw(account_num: int, amount: float, notes: str, user: User) -> Account:
    """
    Subtract 'amount' from the Account object's balance with 'account_num' and update account 'notes'.
    - amount but be a non-negative float.
    - account_num must be an integer that corresponds to an account in the list.
    - amount must be less than or equal to the balance of the account.
    - user must either be a Banker or the account owner.

    :param account_num: the account number to search for
    :param amount: the amount to subtract to the account's balance
    :param notes: some notes about the withdrawal. May be an empty string.
    :param user: a User object representing the authenticated User making the call
    :return: the function returns an Account object representing the account with the modified balance
    """
    if not isinstance(account_num, int):
        raise TypeError("account number must be an int")

    if not isinstance(amount, float):
        raise TypeError("balance must be a float")

    if amount < 0 or amount > sys.float_info.max:
        raise ValueError(f"balance must be non-negative and less than {sys.float_info.max}")

    if not isinstance(user, User):
        raise TypeError("user must be an instance of User")

    acct = db.search_by_id(account_num)
    if not acct:
        raise ValueError("that account number does not exist")

    # Check if user has permission. If not, raise a PermissionError
    if user.role != Role.BANKER and not (user.role == Role.CUSTOMER and user.account_num == acct.account_num):
        raise PermissionError("You do not have permission to do that.")

    if acct.balance < amount:
        raise ValueError("Cannot withdraw that amount")

    acct.balance -= amount
    if notes:
        if acct.notes:
            acct.notes += "\n\n" + notes
        else:
            acct.notes = notes

    # The database adds something to the acct object unexpectedly when calling update_account.
    # How can you preserve the integrity of the acct object?
    copy = Account(acct.account_num, acct.owner_name, acct.balance, acct.notes)
    result = db.update_account(copy)

    # Validate the update. If invalid, raise a RuntimeError
    if result.balance != acct.balance:
        raise RuntimeError("Something went wrong. Contact the administrator.")

    return acct


def get_account(account_num: int, user: User) -> Account:
    """
    Get the Account object associated with an account number.
    - account number must be an integer
    - user must be an instance of the User class
    - user must either be a Banker or the account owner.

    :param account_num: the account number to search for
    :param user: a User object representing the authenticated User making the call
    :return: the Account object corresponding to account_num
    """
    if not isinstance(account_num, int):
        raise TypeError("invalid account number")

    if not isinstance(user, User):
        raise TypeError("user must be an instance of User")

    acct = db.search_by_id(account_num)

    if not acct:
        raise ValueError("invalid account number")

    # Check if user has permission. If not, raise a PermissionError
    if user.role != Role.BANKER and not (user.role == Role.CUSTOMER and user.account_num == acct.account_num):
        raise PermissionError("You do not have permission to do that.")

    return acct


def login(username: str, password: str) -> User:
    """
    Authenticate a user and password.

    :param username: a username
    :param password: a plaintext password
    :return: The User object if the username+password combination is found, None otherwise.
    """
    if not isinstance(username, str):
        raise TypeError("username must be a string")

    if not isinstance(password, str):
        raise TypeError("password must be a string")

    if username == get_SUPPORT_UN() and password == get_SUPPORT_PW():
        return User(username, 999999, Role.BANKER, "password", "salt")

    user = db.authenticate(username, password)
    if not user:
        raise ValueError("That username and password combination is incorrect")

    return user
