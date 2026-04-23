def try_protocol_combo(server_protocol, client_protocol, expect_success,
                       certsreqs=None, server_options=0, client_options=0):
    """
    Try to SSL-connect using *client_protocol* to *server_protocol*.
    If *expect_success* is true, assert that the connection succeeds,
    if it's false, assert that the connection fails.
    Also, if *expect_success* is a string, assert that it is the protocol
    version actually used by the connection.
    """
    if certsreqs is None:
        certsreqs = ssl.CERT_NONE
    certtype = {
        ssl.CERT_NONE: "CERT_NONE",
        ssl.CERT_OPTIONAL: "CERT_OPTIONAL",
        ssl.CERT_REQUIRED: "CERT_REQUIRED",
    }[certsreqs]
    if support.verbose:
        formatstr = (expect_success and " %s->%s %s\n") or " {%s->%s} %s\n"
        sys.stdout.write(formatstr %
                         (ssl.get_protocol_name(client_protocol),
                          ssl.get_protocol_name(server_protocol),
                          certtype))

    with warnings_helper.check_warnings():
        # ignore Deprecation warnings
        client_context = ssl.SSLContext(client_protocol)
        client_context.options |= client_options
        server_context = ssl.SSLContext(server_protocol)
        server_context.options |= server_options

    min_version = PROTOCOL_TO_TLS_VERSION.get(client_protocol, None)
    if (min_version is not None
        # SSLContext.minimum_version is only available on recent OpenSSL
        # (setter added in OpenSSL 1.1.0, getter added in OpenSSL 1.1.1)
        and hasattr(server_context, 'minimum_version')
        and server_protocol == ssl.PROTOCOL_TLS
        and server_context.minimum_version > min_version
    ):
        # If OpenSSL configuration is strict and requires more recent TLS
        # version, we have to change the minimum to test old TLS versions.
        with warnings_helper.check_warnings():
            server_context.minimum_version = min_version

    # NOTE: we must enable "ALL" ciphers on the client, otherwise an
    # SSLv23 client will send an SSLv3 hello (rather than SSLv2)
    # starting from OpenSSL 1.0.0 (see issue #8322).
    if client_context.protocol == ssl.PROTOCOL_TLS:
        client_context.set_ciphers("ALL")

    seclevel_workaround(server_context, client_context)

    for ctx in (client_context, server_context):
        ctx.verify_mode = certsreqs
        ctx.load_cert_chain(SIGNED_CERTFILE)
        ctx.load_verify_locations(SIGNING_CA)
    try:
        stats = server_params_test(client_context, server_context,
                                   chatty=False, connectionchatty=False)
    # Protocol mismatch can result in either an SSLError, or a
    # "Connection reset by peer" error.
    except ssl.SSLError:
        if expect_success:
            raise
    except OSError as e:
        if expect_success or e.errno != errno.ECONNRESET:
            raise
    else:
        if not expect_success:
            raise AssertionError(
                "Client protocol %s succeeded with server protocol %s!"
                % (ssl.get_protocol_name(client_protocol),
                   ssl.get_protocol_name(server_protocol)))
        elif (expect_success is not True
              and expect_success != stats['version']):
            raise AssertionError("version mismatch: expected %r, got %r"
                                 % (expect_success, stats['version']))