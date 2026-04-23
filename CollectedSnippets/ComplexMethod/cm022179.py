def mocked_requests(*args, **kwargs):
    """Mock requests.get invocations."""

    class MockResponse:
        """Class to represent a mocked response."""

        def __init__(self, json_data, status_code) -> None:
            """Initialize the mock response class."""
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            """Return the json of the response."""
            return self.json_data

        @property
        def content(self):
            """Return the content of the response."""
            return self.json()

        def raise_for_status(self):
            """Raise an HTTPError if status is not OK."""
            if self.status_code != HTTPStatus.OK:
                raise requests.HTTPError(self.status_code)

    data = kwargs.get("data")
    # pylint: disable-next=global-statement
    global FIRST_CALL  # noqa: PLW0603

    if data and data.get("username", None) == INVALID_USERNAME:
        # deliver an invalid token
        return MockResponse({"code": "401", "msg": "Invalid token"}, 200)
    if data and data.get("username", None) == TOKEN_TIMEOUT_USERNAME:
        # deliver an expired token
        return MockResponse(
            {
                "url": "/cgi-bin/luci/;stok=ef5860/web/home",
                "token": "timedOut",
                "code": "0",
            },
            200,
        )
    if str(args[0]).startswith(URL_AUTHORIZE):
        # deliver an authorized token
        return MockResponse(
            {
                "url": "/cgi-bin/luci/;stok=ef5860/web/home",
                "token": "ef5860",
                "code": "0",
            },
            200,
        )
    if str(args[0]).endswith(f"timedOut/{URL_LIST_END}") and FIRST_CALL is True:
        FIRST_CALL = False
        # deliver an error when called with expired token
        return MockResponse({"code": "401", "msg": "Invalid token"}, 200)
    if str(args[0]).endswith(URL_LIST_END):
        # deliver the device list
        return MockResponse(
            {
                "mac": "1C:98:EC:0E:D5:A4",
                "list": [
                    {
                        "mac": "23:83:BF:F6:38:A0",
                        "oname": "12255ff",
                        "isap": 0,
                        "parent": "",
                        "authority": {"wan": 1, "pridisk": 0, "admin": 1, "lan": 0},
                        "push": 0,
                        "online": 1,
                        "name": "Device1",
                        "times": 0,
                        "ip": [
                            {
                                "downspeed": "0",
                                "online": "496957",
                                "active": 1,
                                "upspeed": "0",
                                "ip": "192.168.0.25",
                            }
                        ],
                        "statistics": {
                            "downspeed": "0",
                            "online": "496957",
                            "upspeed": "0",
                        },
                        "icon": "",
                        "type": 1,
                    },
                    {
                        "mac": "1D:98:EC:5E:D5:A6",
                        "oname": "CdddFG58",
                        "isap": 0,
                        "parent": "",
                        "authority": {"wan": 1, "pridisk": 0, "admin": 1, "lan": 0},
                        "push": 0,
                        "online": 1,
                        "name": "Device2",
                        "times": 0,
                        "ip": [
                            {
                                "downspeed": "0",
                                "online": "347325",
                                "active": 1,
                                "upspeed": "0",
                                "ip": "192.168.0.3",
                            }
                        ],
                        "statistics": {
                            "downspeed": "0",
                            "online": "347325",
                            "upspeed": "0",
                        },
                        "icon": "",
                        "type": 0,
                    },
                ],
                "code": 0,
            },
            200,
        )
    _LOGGER.debug("UNKNOWN ROUTE")
    return None