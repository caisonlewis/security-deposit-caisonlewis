"""
A simple HTTP server that provides a web interface to bank.py
"""
import json
import re
import socket
import time
from pathlib import Path
from typing import Dict

import bleach
import bank
import http_responses

import http_utils
from http_session_manager import HttpSessionManager

_SESSION_ID = 'SD-SessionID'


def do_get_account_info(resource: str, headers: Dict[str, str]) -> http_responses.OK:
    """
    Process GET method requests for the /accountdetails resource. The request must contain account_num parameters.

    :param resource: the requested resource with query parameters, e.g., /accountdetails?account_num=123456
    :param headers: the HTTP request headers as a field:value dictionary
    :return: OK response containing JSON of the account details.
    """
    # Authenticate the request using the Cookie in the headers
    user_token = _session_manager.authenticate(headers)

    # Extract the query parameters from the resource string
    query = resource.partition('?')[2]
    params = http_utils.convert_query_params_to_dictionary(query)

    # Validate query parameter values
    if 'account_num' not in params or not params['account_num'].isdecimal():
        raise http_responses.BadRequest("account_num parameter value can only be digits")

    account_num = int(bleach.clean(params['account_num']))
    try:
        acct = bank.get_account(account_num, user_token)
    except ValueError as verr:
        raise http_responses.BadRequest(verr)
    except PermissionError:
        raise http_responses.Forbidden("You do not have permission to access that account.")
    except RuntimeError:
        raise http_responses.InternalServerError("A runtime error occurred. Try again.")

    html = f"""<!DOCTYPE html>
            <HTML lang="en">
                <head>
                    <meta charset="UTF-8">
                    <title>Account Lookup Results</title>
                </head>
                <body>
                    <h1>Results</h1>
                    <p><b>Account number: </b> {acct.account_num}</p>
                    <p><b>Owner: </b> {acct.owner_name}</p>
                    <p><b>Balance: </b> {acct.balance}</p>
                    <p><b>Notes: </b> {acct.notes}</p>
                </body>
            </HTML>"""
    return http_responses.OK(html)


def do_create_account(headers: Dict[str, str], request_body: str) -> http_responses.OK:
    """
    Process POST method requests for the /createaccount.

    :param headers: the HTTP request headers as a field:value dictionary
    :param request_body: The request body must contain owner_name and balance parameters.
    :return: OK response containing JSON data of the newly-created account.
    """
    # Authenticate the request using the Cookie in the headers
    user_token = _session_manager.authenticate(headers)

    # Extract query parameters from the request body. Assume they are the request body.
    params = http_utils.convert_query_params_to_dictionary(request_body)

    # Validate the query parameters
    if 'owner_name' not in params:
        raise http_responses.BadRequest("missing required parameter owner_name")

    if 'balance' not in params:
        raise http_responses.BadRequest("missing required parameter balance")

    try:
        balance = float(params['balance'])
    except ValueError:
        raise http_responses.BadRequest("balance must be a float")

    owner_name = bleach.clean(params['owner_name'])
    try:
        # Call the bank.py logic and handle raised exceptions
        acct = bank.create_account(owner_name, balance, user_token)
        # Convert the returned Account object to JSON and wrap in an OK response
        return http_responses.OK(bleach.clean(json.dumps(vars(acct), indent=4)))
    except (TypeError, ValueError) as err:
        raise http_responses.BadRequest(err)
    except PermissionError:
        raise http_responses.Forbidden("You do not have permission to do that.")
    except RuntimeError:
        raise http_responses.InternalServerError("A runtime error occurred. Try again.")


def do_deposit(headers: Dict[str, str], request_body: str) -> http_responses.OK:
    """
    Process POST method requests for the /deposit.

    :param headers: the HTTP request headers as a field:value dictionary
    :param request_body: The request body must contain account_num and amount parameters.
    :return: OK response containing JSON data of the updated account.
    """
    # Authenticate the request using the Cookie in the headers
    user_token = _session_manager.authenticate(headers)

    # Extract query parameters from the request body. Assume they are the request body.
    params = http_utils.convert_query_params_to_dictionary(request_body)

    # Validate the query parameters
    if 'account_num' not in params or not params['account_num'].isdecimal():
        raise http_responses.BadRequest("account_num parameter value can only be digits")

    if 'amount' not in params:
        raise http_responses.BadRequest("missing required parameter amount")

    try:
        amount = float(params['amount'])
    except ValueError:
        raise http_responses.BadRequest("amount must be an float")

    notes = bleach.clean(params.get('notes', ''))
    account_num = int(bleach.clean(params['account_num']))
    try:
        # Call the bank.py logic and handle raised exceptions
        acct = bank.deposit(account_num, amount, notes, user_token)
        # Convert the returned Account object to JSON and wrap in an OK response
        return http_responses.OK(bleach.clean(json.dumps(vars(acct), indent=4)))
    except (TypeError, ValueError) as err:
        raise http_responses.BadRequest(err)
    except PermissionError:
        raise http_responses.Forbidden("You do not have permission to do that.")
    except RuntimeError:
        raise http_responses.InternalServerError("A runtime error occurred. Try again.")


def do_withdraw(headers: Dict[str, str], request_body: str) -> http_responses.OK:
    """
    Process POST method requests for the /withdraw.

    :param headers: the HTTP request headers as a field:value dictionary
    :param request_body: The request body must contain account_num and amount parameters.
    :return: OK response containing JSON data of the updated account.
    """
    # Authenticate the request using the Cookie in the headers
    user_token = _session_manager.authenticate(headers)

    # Extract query parameters from the request body. Assume they are the request body.
    params = http_utils.convert_query_params_to_dictionary(request_body)

    # Validate query parameters
    if 'account_num' not in params or not params['account_num'].isdecimal():
        raise http_responses.BadRequest("account_num parameter value can only be digits")

    if 'amount' not in params:
        raise http_responses.BadRequest("missing required parameter amount")

    try:
        amount = float(params['amount'])
    except ValueError:
        raise http_responses.BadRequest("amount must be an float")

    account_num = int(bleach.clean(params['account_num']))
    notes = bleach.clean(params.get('notes', ''))
    try:
        # Call the bank.py logic and handle raised exceptions
        acct = bank.withdraw(account_num, amount, notes, user_token)
        # Convert the returned Account object to JSON and wrap in an OK response
        return http_responses.OK(bleach.clean(json.dumps(vars(acct), indent=4)))
    except (TypeError, ValueError) as err:
        raise http_responses.BadRequest(err)
    except PermissionError:
        raise http_responses.Forbidden("You do not have permission to do that.")
    except RuntimeError:
        raise http_responses.InternalServerError("A runtime error occurred. Try again.")


# _sessions = {}
_session_manager = HttpSessionManager()


def do_login(headers: Dict[str, str], request_body: str) -> http_responses.OK:
    # Extract query parameters from the request body. Assume they are the request body.
    params = http_utils.convert_query_params_to_dictionary(request_body)

    # Validate query parameters
    if 'username' not in params:
        raise http_responses.BadRequest("missing required username")

    if 'password' not in params:
        raise http_responses.BadRequest("missing required password")

    username = bleach.clean(params['username'])
    password = bleach.clean(params['password'])
    try:
        user = bank.login(username, password)
        cookie = _session_manager.create_session(user, headers)
    except ValueError as verr:
        raise http_responses.Forbidden(verr) from verr

    response = do_get_file_resource('/menu.html', headers)
    response.headers = [str(cookie)]
    return response


def do_logout(headers: Dict[str, str]) -> http_responses.OK:
    html = """<!DOCTYPE html>
                <HTML lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <title>You are logged out</title>
                    </head>
                    <body>
                        <h1>You are logged out</h1>
                    </body>
                </HTML>"""

    if 'Cookie' in headers:
        cookie = _session_manager.delete_session(headers)
        return http_responses.OK(body=html, headers=[str(cookie)])

    return http_responses.OK(body=html)


def handle_post(resource: str, headers: Dict[str, str], request_body: str) -> http_responses.OK:
    """
    Call the appropriate function to handle a POST request based on the requested resource.

    :param resource: the requested resource as a string
    :param headers: the HTTP request headers as a field:value dictionary
    :param request_body: the request body as a list of strings
    :return: OK status returned by one of the function calls.
    """
    if resource == '/createaccount':
        return do_create_account(headers, request_body)
    if resource == '/deposit':
        return do_deposit(headers, request_body)
    if resource == '/withdraw':
        return do_withdraw(headers, request_body)
    if resource == '/login':
        return do_login(headers, request_body)

    raise http_responses.NotFound("Invalid resource.")


html_file_pattern = re.compile(r'^.+\.(html|htm|css)$', re.ASCII | re.IGNORECASE)


def do_get_file_resource(resource: str, headers: Dict[str, str]) -> http_responses.OK:
    """
    Handle the basic GET request for an HTML resource

    :param resource: the resource string
    :param headers: the headers
    :return: OK status with the HTML as the response body.
    """
    if resource == "/":
        filename = "menu.html"
    else:
        filename = resource[1:]

    if html_file_pattern.match(filename):
        path = Path("html") / filename
        if path.is_file():
            with open(path) as infile:
                html_data = infile.read()
                return http_responses.OK(html_data)

    raise http_responses.NotFound("Invalid resource.")


def handle_get(resource: str, headers: Dict[str, str]) -> http_responses.OK:
    """
    Call the appropriate function to handle a GET request based on the requested resource.

    :param resource: the requested resource as a string
    :param headers: the HTTP request headers as a field:value dictionary
    :return: OK status with an appropriate response body
    """

    # Handle the special /accountdetails GET request, which should have query parameters
    # Example: /accountdetails?account_num=935370
    if resource.startswith("/accountdetails"):
        return do_get_account_info(resource, headers)

    if resource == "/logout":
        return do_logout(headers)

    # Otherwise, default the GET request as a request for a file.
    return do_get_file_resource(resource, headers)


HOST = '127.0.0.1'  # '0.0.0.0'
PORT = 9999


def main():
    """
    The main loop of the webserver
    """
    # TODO: Dictionary to help track client request rates. The keys should be the client IP address.
    clients_and_rates = {}
    count = 0
    start_time = time.time()
    end_time = start_time + 900

    # Create a new socket that by default uses TCP/IP
    with socket.socket() as sock:
        # Tells the OS to reuse the socket if we restart the program
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, PORT))
        sock.listen()

        sock_name = sock.getsockname()
        print(f"Listening at: {sock_name}, http://{sock_name[0]}:{sock_name[1]}")

        while True:


            # Wait for clients to connect
            client_connection, client_address = sock.accept()
            print("\nClient address:", client_address)

            try:
                # TODO: Implement rate-limiting logic here. raise a TooManyRequests() error when appropriate.
                RATE_WINDOW = 900 # 900sec = 15min
                RATE_LIMIT = 10
                count += 1
                clients_and_rates.update({client_connection : count})

                # reset time frame
                if start_time == end_time:
                    clients_and_rates.clear()
                # check for number of requests within time frame
                if clients_and_rates[client_connection] >= 10:
                    raise Exception('HTTP Error 429 TOO MANY REQUESTS')


                # Get the client request
                request = client_connection.recv(2048)
                request = request.decode()

                time.sleep(0.1)  # Introduce an artificial wait time of 0.1 seconds for each request.

                # Pull apart the HTTP request into its constituent parts.
                method, resource, protocol, headers, body = http_utils.parse_request(request)
                print(f"method: {method}\n"
                      f"resource: {resource}\n"
                      f"protocol: {protocol}\n"
                      f"headers: {headers}\n"
                      f"body: {body}")

                if method == 'GET':
                    response = handle_get(resource, headers)
                elif method == 'POST':
                    response = handle_post(resource, headers, body)
                else:
                    # Default response for HTTP Methods the server doesn't handle.
                    response = http_responses.NotImplementedStatus()

                # CORS support - required for AJAX requests and certain file resources in modern browsers
                if 'Origin' in headers:
                    response.headers.append('Access-Control-Allow-Origin: ' + headers['Origin'])
            except http_responses.HttpErrorResponse as err:
                response = err

            client_connection.sendall(str(response).encode())
            client_connection.close()



if __name__ == "__main__":
    main()
