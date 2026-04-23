def testing_context(server_cert=SIGNED_CERTFILE, *, server_chain=True,
                    client_cert=None):
    """Create context

    client_context, server_context, hostname = testing_context()
    """
    global _TEST_CONTEXT
    if USE_SAME_TEST_CONTEXT:
        if _TEST_CONTEXT is not None:
            return _TEST_CONTEXT

    if server_cert == SIGNED_CERTFILE:
        hostname = SIGNED_CERTFILE_HOSTNAME
    elif server_cert == SIGNED_CERTFILE2:
        hostname = SIGNED_CERTFILE2_HOSTNAME
    elif server_cert == NOSANFILE:
        hostname = NOSAN_HOSTNAME
    else:
        raise ValueError(server_cert)

    client_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    client_context.load_verify_locations(SIGNING_CA)

    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_context.load_cert_chain(server_cert)
    if server_chain:
        server_context.load_verify_locations(SIGNING_CA)

    if client_cert:
        client_context.load_cert_chain(client_cert)
        server_context.verify_mode = ssl.CERT_REQUIRED

    if USE_SAME_TEST_CONTEXT:
        if _TEST_CONTEXT is not None:
            _TEST_CONTEXT = client_context, server_context, hostname

    return client_context, server_context, hostname