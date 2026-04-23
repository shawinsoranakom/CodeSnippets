def test_Request_open(urlopen_mock, install_opener_mock):
    r = Request().open('GET', 'https://ansible.com/')
    args = urlopen_mock.call_args[0]
    assert args[1] is None  # data, this is handled in the Request not urlopen
    assert args[2] == 10  # timeout

    req = args[0]
    assert req.headers == {}
    assert req.data is None
    assert req.get_method() == 'GET'

    opener = install_opener_mock.call_args[0][0]
    handlers = opener.handlers

    expected_handlers = (
        HTTPRedirectHandler(),
    )

    found_handlers = []
    for handler in handlers:
        if handler.__class__.__name__ == 'HTTPRedirectHandler':
            found_handlers.append(handler)

    assert len(found_handlers) == len(expected_handlers)