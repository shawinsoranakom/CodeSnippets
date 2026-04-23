def make_test_context(
    *,
    server_side=False,
    check_hostname=None,
    cert_reqs=ssl.CERT_NONE,
    ca_certs=None, certfile=None, keyfile=None,
    ciphers=None, ciphersuites=None,
    min_version=None, max_version=None,
):
    if server_side:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    else:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    if check_hostname is None:
        if cert_reqs == ssl.CERT_NONE:
            context.check_hostname = False
    else:
        context.check_hostname = check_hostname

    if cert_reqs is not None:
        context.verify_mode = cert_reqs

    if ca_certs is not None:
        context.load_verify_locations(ca_certs)
    if certfile is not None or keyfile is not None:
        context.load_cert_chain(certfile, keyfile)

    if ciphers is not None:
        context.set_ciphers(ciphers)
    if ciphersuites is not None:
        context.set_ciphersuites(ciphersuites)

    if min_version is not None:
        context.minimum_version = min_version
    if max_version is not None:
        context.maximum_version = max_version

    return context