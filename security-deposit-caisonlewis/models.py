"""
Classes used to represent data objects in our banking system.
"""
from enum import Enum


class Account:
    """
    A simple class representing a bank account.
    """

    def __init__(self, account_num, owner_name, balance, notes=None):
        self.account_num = int(account_num)
        self.owner_name = str(owner_name)
        self.balance = float(balance)
        self.notes = notes

    def __str__(self):
        return f"Acct#: {self.account_num}, Owner: {self.owner_name}, Balance: {self.balance:.2f}, Notes: {self.notes}"

    def __repr__(self):
        return f"Account({self.account_num}, {self.owner_name}, {self.balance}, {self.notes})"


class Role(Enum):
    """
    an Enum for representing the different roles in the system.
    """
    CUSTOMER = 1
    BANKER = 2


class User:
    """
    A class representing a logged-in User
    """

    def __init__(self, username, account_num, role, password, salt):
        self.username = username
        self.account_num = int(account_num)
        self.role = role
        self.password = password
        self.salt = salt

    def __str__(self):
        return f"Username: {self.username}, Acct#: {self.account_num}, " \
               f"Role: {self.role}, Password: {self.password}, Salt: {self.salt}"

    def __repr__(self):
        return f"User({self.username}, {self.account_num}, {self.role}, {self.password}, {self.salt})"
