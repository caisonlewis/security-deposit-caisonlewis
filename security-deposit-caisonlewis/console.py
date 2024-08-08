"""
A console interface for the banking application.
"""
import sys

import bank
from models import User


def do_create(user: User) -> None:
    """
    Get user input and make a call to create a user
    :param user: a User object representing the authenticated user at the console
    :return: None
    """
    print("Create an account")
    name = input("Input an owner name: ")

    try:
        balance = float(input("Input an initial balance: "))
    except ValueError:
        print("You must enter a numeric balance.")
        return

    try:
        account = bank.create_account(name, balance, user)
        print("Success! The following account has been created:", account)
    except (TypeError, ValueError, PermissionError) as err:
        print("Error:", err)
    except RuntimeError as rte:
        print("RUNTIME ERROR", rte)


def do_deposit(user: User) -> None:
    """
    Get user input and make a call to deposit money into an account
    :param user: a User object representing the authenticated user at the console
    :return: None
    """

    print("Deposit into an account")

    try:
        acct_num = int(input("Input the account number: "))
    except ValueError:
        print("Account number must be an integer.")
        return

    try:
        amount = float(input("Input an amount to deposit: "))
    except ValueError:
        print("You must enter a numeric amount.")
        return

    notes = input("(Optional) Enter a note, or hit (Enter) to skip: ").strip()

    try:
        account = bank.deposit(acct_num, amount, notes, user)
        print(f"Success! Account number {account.account_num} new balance is {account.balance:.2f}.")
    except (TypeError, ValueError, PermissionError) as err:
        print("Error:", err)
    except RuntimeError as rte:
        print("RUNTIME ERROR: Something awful occurred while performing a deposit.", rte)


def do_withdraw(user: User) -> None:
    """
    Get user input and make a call to withdraw money from an account
    :param user: a User object representing the authenticated user at the console
    :return: None
    """
    print("Withdraw from an account")

    try:
        acct_num = int(input("Input the account number: "))
    except ValueError:
        print("Account number must be an integer.")
        return

    try:
        amount = float(input("Input an amount to withdraw: "))
    except ValueError:
        print("You must enter a numeric amount.")
        return

    notes = input("(Optional) Enter a note, or hit (Enter) to skip: ").strip()

    try:
        account = bank.withdraw(acct_num, amount, notes, user)
        print(f"Success! Account number {account.account_num} new balance is {account.balance:.2f}.")
    except (TypeError, ValueError, PermissionError) as err:
        print("Error:", err)
    except RuntimeError as rte:
        print("RUNTIME ERROR: Something awful occurred while performing a withdrawal.", rte)


def do_get_account(user: User) -> None:
    """
    Get user input and make a call to look up account details by account number
    :param user: a User object representing the authenticated user at the console
    :return: None
    """
    print("Get account details")

    try:
        acct_num = int(input("Input the account number: "))
    except ValueError:
        print("Account number must be an integer.")
        return

    try:
        print(bank.get_account(acct_num, user))
    except (TypeError, ValueError, PermissionError) as err:
        print("Error:", err)


def main() -> None:
    """
    The main function
    """
    print("Welcome to Security Deposit!")

    user = None
    print("Login, or hit Enter to exit")
    while not user:
        username = input("Enter your username: ")
        password = input("Enter your password: ")
        if not username:
            print("Exiting...")
            sys.exit(0)
        else:
            try:
                user = bank.login(username, password)
            except ValueError:
                print("Login failed. Try again, or hit Enter to exit.")

    options = {
        "1": ["Create an account", do_create],
        "2": ["Deposit", do_deposit],
        "3": ["Withdraw", do_withdraw],
        "4": ["Get account details", do_get_account]
    }

    while True:
        print("--------")
        print("Select a number, or hit Enter to exit:")
        for num, option in options.items():
            print(f"{num}) {option[0]}")

        choice = input()
        if not choice:
            break
        if choice not in options:
            print("Invalid entry, pick again.")
            continue
        options[choice][1](user)


if __name__ == "__main__":
    main()
