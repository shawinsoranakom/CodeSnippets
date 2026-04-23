def test_Request_open_no_validate_certs(urlopen_mock, install_opener_mock, mocker):
    do_open = mocker.patch.object(urllib.request.HTTPSHandler, 'do_open')

    r = Request().open('GET', 'https://ansible.com/', validate_certs=False)

    opener = install_opener_mock.call_args[0][0]
    handlers = opener.handlers

    ssl_handler = None
    for handler in handlers:
        if isinstance(handler, urllib.request.HTTPSHandler):
            ssl_handler = handler
            break

    assert ssl_handler is not None

    ssl_handler.https_open(None)
    args = do_open.call_args[0]
    cls = args[0]
    assert cls is http.client.HTTPSConnection

    context = ssl_handler._context
    # Differs by Python version
    # assert context.protocol == ssl.PROTOCOL_SSLv23
    if ssl.OP_NO_SSLv2:
        assert context.options & ssl.OP_NO_SSLv2
    assert context.options & ssl.OP_NO_SSLv3
    assert context.verify_mode == ssl.CERT_NONE
    assert context.check_hostname is False