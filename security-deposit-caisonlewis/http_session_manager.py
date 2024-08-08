import base64
import os
import pickle  # nosec
import time
from dataclasses import dataclass
from http.cookies import SimpleCookie
from pathlib import Path
from typing import Dict

from http_responses import Unauthorized
from models import User

_SESSION_ID = 'SD-SessionID'
_SESSION_FILE = Path('database') / 'sessions.pickle'


@dataclass
class Session:
    user: User
    expiration: float = 0


class HttpSessionManager:
    def __init__(self):
        self._sessions = {}
        if _SESSION_FILE.is_file():
            with open(_SESSION_FILE, "rb") as file:
                self._sessions = pickle.load(file)  # nosec

    def _write_sessions(self):
        with open(_SESSION_FILE, "wb") as file:
            pickle.dump(self._sessions, file)

    def create_session(self, user: User, headers: Dict[str, str]) -> SimpleCookie:
        # Invalidate the old session id if one exists
        if 'Cookie' in headers:
            cookie = SimpleCookie()
            cookie.load(headers['Cookie'])
            if _SESSION_ID in cookie and cookie[_SESSION_ID].value in self._sessions:
                del self._sessions[cookie[_SESSION_ID].value]

        session_id = base64.b64encode(os.urandom(128)).decode()
        expiration = time.time() + 3600  # The login token lasts for 1 hour
        cookie = SimpleCookie()
        cookie[_SESSION_ID] = session_id
        cookie[_SESSION_ID]['expires'] = expiration
        cookie[_SESSION_ID]['path'] = '/'

        self._sessions[session_id] = Session(user, expiration)
        self._write_sessions()
        return cookie

    def delete_session(self, headers: Dict[str, str]) -> SimpleCookie:
        # Extract and decode the credentials from the request header.
        cookie = SimpleCookie()
        cookie.load(headers['Cookie'])

        # Make sure security-deposit cookie is present, and that the token is in the current list of sessions.
        if _SESSION_ID in cookie and cookie[_SESSION_ID].value in self._sessions:
            del self._sessions[cookie[_SESSION_ID].value]

        # Invalidate the cookie for the client before sending the response.
        cookie[_SESSION_ID] = 'deleted'
        cookie[_SESSION_ID]['expires'] = 0
        self._write_sessions()
        return cookie

    def authenticate(self, headers: Dict[str, str]) -> User:
        """
        Extract session id from client cookie, and make sure that the session id is active in the current dict of _sessions
        and not expired. If the session id is valid, then return the User object associated with the session id.

        An Unauthorized response status is raised:
         - if the cookie does not contain the session id,
         - the session id is not in the server's _sessions dictionary.
         - the session id has expired

        :param headers: the HTTP request headers as a field:value dictionary
        :return: a User object containing the authenticated user's info
        """

        # Check to see if Cookie header exists.
        if 'Cookie' not in headers:
            raise Unauthorized("Login required")

        # Extract and decode the credentials from the request header.
        cookie = SimpleCookie()
        cookie.load(headers['Cookie'])

        # Make sure security-deposit cookie is present, and that the token is in the current list of sessions.
        if _SESSION_ID not in cookie or cookie[_SESSION_ID].value not in self._sessions:
            raise Unauthorized("Login required")

        session_id = cookie[_SESSION_ID].value
        # Check to see if the session id / cookie has expired.
        if self._sessions[session_id].expiration < time.time():
            del self._sessions[session_id]
            # Invalidate the cookie for the client before sending the response.
            cookie[_SESSION_ID] = 'deleted'
            cookie[_SESSION_ID]['expires'] = 0
            raise Unauthorized('Login required.', headers=[str(cookie)])

        # Look up the User object from the session list
        print("Successfully authenticated:", self._sessions[session_id].user)
        self._write_sessions()
        return self._sessions[session_id].user
