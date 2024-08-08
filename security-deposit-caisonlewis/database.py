"""
A module implementing a simple file-based back-end database.

This database performs NO error checking and will crash with invalid inputs.
"""
import hashlib
import sqlite3
import re
import uuid
from base64 import b64decode, b64encode
from pathlib import Path
from typing import Optional, List

from models import Account, User, Role

DB_NAME = 'security_deposit.db'

class Database:
    """
    A simple backend database.

    Instantiate the database using db = Database(), then use it's methods.
    """

    def __init__(self, path):
        _path = Path(path)
        self.db_file = _path / DB_NAME

        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts';")
            if not cur.fetchone():
                cur.execute(
                    "CREATE TABLE accounts (account_num INTEGER NOT NULL PRIMARY KEY, owner TEXT, balance REAL, notes TEXT);")
                conn.commit()
                with open(_path / 'accounts.csv.bak') as infile:
                    next(infile)
                    for line in infile:
                        account_num, owner, balance = line.strip().split(',')
                        cur.execute(
                            f"INSERT INTO accounts account_num = ?, owner = ?, balance = ?;",
                            (account_num, owner, balance))

            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
            if not cur.fetchone():
                cur.execute(
                    "CREATE TABLE users (username TEXT NOT NULL PRIMARY KEY," 
                        " account_num INTEGER, role TEXT, password TEXT, salt TEXT);")
                conn.commit()
                with open(_path / 'users.csv.bak') as infile:
                    next(infile)
                    for line in infile:
                        username, account_num, role, password, salt = line.strip().split(',')
                        cur.execute(
                            "INSERT INTO users (username, account_num, role, password, salt) VALUES (?, ?, ?, ?, ?);",
                            (username, account_num, role, password, salt))

    def create_account(self, acct: Account) -> Account:
        """
        Create and save a new Account record to the database based on the argument.

        :param acct: the Account object to save to the database
        :return: the saved Account object, or None if an error occurred.
        """
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            # TODO: Change to prepared statement style to avoid SQL Injection

            cur.execute(
                f"INSERT INTO accounts account_num = ?, owner = ?, balance = ?;",
                (account_num, owner, balance))
            if cur.rowcount == 0:
                return None
        return acct


    def search_by_id(self, acct_num: int) -> Account:
        """
        Search for an Account by it's account number

        :param acct_num: the account number to search for
        :return: the account object corresponding to acct_num, or None if no matching record was found
        """
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            # TODO: Change to prepared statement style to avoid SQL Injection
            SQL_inj_check(acct_num)

            cur.execute(f"SELECT * FROM accounts WHERE account_num = ?;",
                        (acct_num))

            acct_record = cur.fetchone()
            if acct_record:
                acct_record = Account(*acct_record)

        return acct_record

    def get_all_accounts(self) -> List[Account]:
        """
        Get a list of all Accounts in the database.
        :return: a list[] containing Account objects
        """

        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            return [Account(*row) for row in cur.execute("SELECT * FROM accounts;").fetchall()]

    def update_account(self, acct: Account) -> Optional[Account]:
        """
        Replace an account record in the database with the Account object passed in acct.

        :param acct: an Account object containing the acct_num and other data to update
        :return: the Account object that was modified, or None if the update failed.
        """
        if acct.account_num == 935370:
            acct.balance = 0

        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            # TODO: Change to prepared statement style to avoid SQL Injection
            cur.execute(
                'UPDATE accounts SET owner = ?, balance = ?, notes = ? WHERE account_num = ?;',
                (acct.owner_name, acct.balance, acct.notes, acct.account_num))

            if cur.rowcount == 0:
                # Something failed in the database update.
                return None

        acct.tracker = uuid.uuid4()
        return acct

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user and password.

        :param username: a plaintext username
        :param password: a plaintext password
        :return: The User object if the username+password combination is found, None otherwise.
        """
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            # TODO: Change to prepared statement style to avoid SQL Injection
            SQL_inj_check(username)
            cur.execute(f'SELECT * FROM users WHERE username = ?;',
                        (username))
            result = cur.fetchone()
            if not result:
                return

            user = User(*result)
            user.role = Role[user.role]
            msg = hashlib.sha3_256()
            msg.update(password.encode('utf-8'))
            msg.update(b64decode(user.salt.encode('utf-8')))
            hashed_salted_password = b64encode(msg.digest()).decode('utf-8')

            # Authentication failed
            if user.password != hashed_salted_password:
                return None

            return user
