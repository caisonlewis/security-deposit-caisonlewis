"""
This module contains utility classes for quickly constructing HTTP Responses.
"""

import json

import bleach


class OK:
    """
    200 - OK. For successful HTTP requests.
    Note that OK should be returned if the server is capable of processing the request.
    If the request data are invalid according to the business logic, OK should still be returned along with information
    of what went wrong.
    """

    def __init__(self, body=None, headers=None):
        self.headers = headers
        if not self.headers:
            self.headers = []
        self.headers.append('Vary: Origin')
        self.headers.append('Access-Control-Allow-Methods: GET, POST')
        self.body = str(body)
        try:
            json.loads(self.body)
            self.headers.append('Content-Type: application/json; charset=utf-8')
        except json.JSONDecodeError:
            self.headers.append('Content-Type: text/html; charset=utf-8')

    def __str__(self):
        base = "HTTP/1.1 200 OK\n"
        if self.headers:
            base += '\n'.join(self.headers) + '\n'
        base += '\n'
        if self.body:
            base += self.body
        return base


class HttpErrorResponse(Exception):
    """
    Base class for HTTP error responses (codes 4xx-5xx).

    This responses can be raised as Exceptions.

    Calling str() on instances of this class or any of its subclasses will yield
    a properly formatted HTTP response string.
    """

    def __init__(self, code, reason, body=None, headers=None):
        super().__init__()
        self.code = code
        self.reason = reason
        self.headers = headers
        if not self.headers:
            self.headers = []
        self.headers.append('Content-Type: application/json; charset=utf-8')
        self.body = body

    def __str__(self):
        base = f"HTTP/1.1 {self.code} {self.reason}\n"
        if self.headers:
            base += '\n'.join(self.headers) + '\n'
        base += '\n'
        if self.body:
            base += '{\n' \
                    f'    "code": "{self.code}",\n' \
                    f'    "reason": "{self.reason}",\n' \
                    f'    "error": "{str(self.body)}"\n' \
                    '}'
        return bleach.clean(base)


class BadRequest(HttpErrorResponse):
    """
    400 - Bad Request. Something is wrong with the HTTP request itself, e.g., missing query parameters, missing header.
    This is only if the HTTP server cannot process the request. If the business logic (bank.py) can process the input,
    but finds it erroneous, return OK status with an error message embedded.
    """

    def __init__(self, body=None, headers=None):
        super().__init__(400, "Bad Request", body, headers)


class Unauthorized(HttpErrorResponse):
    """
    401 - Unauthorized. The user needs to authenticate to access that resource.
    A header is added to prompt the client to authenticate using HTTP Basic Authentication.
    """

    def __init__(self, body=None, headers=None):
        if not headers:
            headers = []
        super().__init__(401, "Unauthorized", body, headers)


class Forbidden(HttpErrorResponse):
    """
    403 - Forbidden. User is not authorized to access a resource.
    """

    def __init__(self, body=None, headers=None):
        # with open('html/login.html', 'r') as file:
        #     body = file.read()
        super().__init__(403, "Forbidden", body, headers)


class NotFound(HttpErrorResponse):
    """
    404 - Not Found. The requested resource is not available on the server.
    """

    def __init__(self, body=None, headers=None):
        super().__init__(404, "Not Found", body, headers)


class TooManyRequests(HttpErrorResponse):
    """
    429 - Too Many Requests. The client has sent too many requests in a given amount of time.
    """

    def __init__(self, body=None, headers=None):
        super().__init__(429, "Too Many Requests", body, headers)


class InternalServerError(HttpErrorResponse):
    """
    500 - Internal Server Error. An unanticipated failure in the server code caused an error.
    """

    def __init__(self, body=None, headers=None):
        super().__init__(500, "Internal Server Error", body, headers)


class NotImplementedStatus(HttpErrorResponse):
    """
    501 - Not Implemented. The request method is not supported by the server.
    """

    def __init__(self, body=None, headers=None):
        super().__init__(501, "Not Implemented", body, headers)
