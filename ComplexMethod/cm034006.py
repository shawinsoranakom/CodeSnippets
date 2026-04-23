def make_context(cafile=None, cadata=None, capath=None, ciphers=None, validate_certs=True, client_cert=None,
                 client_key=None):
    if ciphers is None:
        ciphers = []

    if not is_sequence(ciphers):
        raise TypeError('Ciphers must be a list. Got %s.' % ciphers.__class__.__name__)

    context = ssl.create_default_context(cafile=cafile)

    if not validate_certs:
        context.options |= ssl.OP_NO_SSLv3
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    # If cafile is passed, we are only using that for verification,
    # don't add additional ca certs
    if validate_certs and not cafile:
        if not cadata:
            cadata = bytearray()
        cadata.extend(get_ca_certs(capath=capath)[0])
        if cadata:
            context.load_verify_locations(cadata=cadata)

    if ciphers:
        context.set_ciphers(':'.join(map(to_native, ciphers)))

    if client_cert:
        # TLS 1.3 needs this to be set to True to allow post handshake cert
        # authentication. This functionality was added in Python 3.8 and was
        # backported to 3.6.7, and 3.7.1 so needs a check for now.
        if hasattr(context, "post_handshake_auth"):
            context.post_handshake_auth = True

        context.load_cert_chain(client_cert, keyfile=client_key)

    return context