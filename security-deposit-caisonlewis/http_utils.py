"""
This module provides some convenience methods for extracting data from HTTP requests.
"""
import re
from typing import Dict, List, Tuple
from urllib.parse import unquote_plus, unquote

from http_responses import BadRequest

# Authorization header values are Base64 encoded followed by an optional realm. Format:
# ^Basic <Base64 credentials> <realm info>$
BASIC_AUTH_VALUE = re.compile(r"^Basic [A-Za-z0-9+/]+={0,2}\s*.*$", re.ASCII)


def convert_query_params_to_dictionary(query: str) -> Dict[str, str]:
    """
    Take a query string, e.g., param1=value1&param2=value2, and return a dictionary of param: value pairs.
    :param query: the query string
    :return: the dictionary of param:value pairs.
    """
    if not query:
        raise BadRequest("No query to process.")
    params = query.split('&')
    result = {}
    for param in params:
        param, sep, value = param.partition('=')
        if not sep:
            raise BadRequest("Malformed query parameter(s). This app supports only <key>=<value> parameter form.")
        result[unquote_plus(param)] = unquote_plus(value)

    return result


VALID_REQUEST_LINE_PATTERN = re.compile(r"^(OPTIONS|GET|HEAD|POST|PUT|DELETE|TRACE|CONNECT) \S+ HTTP/(1.0|1.1|2.0)$",
                                        re.ASCII)


def parse_request(request: str) -> Tuple[str, str, str, Dict[str, str], List[str]]:
    """
    Take an HTTP request and break it into it's constituent parts.
    This method returns multiple values in the following order:
        1) the HTTP method
        2) the requested resource
        3) the protocol
        4) a dictionary of headers with <field name>:<field value> pairs
        5) a list of strings of the request body contents where each element is one line of the request body.
    :param request: the full HTTP request string
    :return: the method, resource, protocol, header dictionary, and body line list
    """
    lines = request.splitlines()

    if not lines:
        raise BadRequest("Request is empty.")

    request_line = lines[0]
    if not re.match(VALID_REQUEST_LINE_PATTERN, request_line):
        raise BadRequest("Invalid request line syntax")

    method, resource, protocol = request_line.split(' ')
    resource = unquote_plus(resource)
    try:
        # There is a mandatory empty line between headers and body, but both headers and body are optional.
        # <request line>\n<headers>\n<body>
        # Or, <request line>\n<headers>\n
        # Or, <request line>\n\n<body>
        # Or, <request line>\n\n
        crlf = lines.index('')
    except ValueError as verr:
        raise BadRequest('Missing mandatory CRLF.') from verr
    header_lst = lines[1:crlf]
    headers = {}
    for header in header_lst:
        field_name, sep, field_value = header.partition(':')
        if not sep or not field_value:
            raise BadRequest("Malformed HTTP header:" + header)
        headers[unquote(field_name.strip())] = unquote(field_value.strip())
    body = unquote_plus('\n'.join(lines[crlf + 1:]))
    return method, resource, protocol, headers, body
