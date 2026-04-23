def get_ca_certs(cafile=None, capath=None):
    # tries to find a valid CA cert in one of the
    # standard locations for the current distribution

    # Using a dict, instead of a set for order, the value is meaningless and will be None
    # Not directly using a bytearray to avoid duplicates with fast lookup
    cadata = {}

    # If cafile is passed, we are only using that for verification,
    # don't add additional ca certs
    if cafile:
        paths_checked = [cafile]
        with open(to_bytes(cafile, errors='surrogate_or_strict'), 'r', errors='surrogateescape') as f:
            for pem in extract_pem_certs(f.read()):
                b_der = ssl.PEM_cert_to_DER_cert(pem)
                cadata[b_der] = None
        return bytearray().join(cadata), paths_checked

    default_verify_paths = ssl.get_default_verify_paths()
    default_capath = default_verify_paths.capath
    paths_checked = {default_capath or default_verify_paths.cafile}

    if capath:
        paths_checked.add(capath)

    system = to_text(platform.system(), errors='surrogate_or_strict')
    # build a list of paths to check for .crt/.pem files
    # based on the platform type
    if system == u'Linux':
        paths_checked.add('/etc/pki/ca-trust/extracted/pem')
        paths_checked.add('/etc/pki/tls/certs')
        paths_checked.add('/usr/share/ca-certificates/cacert.org')
    elif system == u'FreeBSD':
        paths_checked.add('/usr/local/share/certs')
    elif system == u'OpenBSD':
        paths_checked.add('/etc/ssl')
    elif system == u'NetBSD':
        paths_checked.add('/etc/openssl/certs')
    elif system == u'SunOS':
        paths_checked.add('/opt/local/etc/openssl/certs')
    elif system == u'AIX':
        paths_checked.add('/var/ssl/certs')
        paths_checked.add('/opt/freeware/etc/ssl/certs')
    elif system == u'Darwin':
        paths_checked.add('/usr/local/etc/openssl')

    # fall back to a user-deployed cert in a standard
    # location if the OS platform one is not available
    paths_checked.add('/etc/ansible')

    # for all of the paths, find any  .crt or .pem files
    # and compile them into single temp file for use
    # in the ssl check to speed up the test
    for path in paths_checked:
        if not path or path == default_capath or not os.path.isdir(path):
            continue

        for f in os.listdir(path):
            full_path = os.path.join(path, f)
            if os.path.isfile(full_path) and os.path.splitext(f)[1] in {'.pem', '.cer', '.crt'}:
                try:
                    with open(full_path, 'r', errors='surrogateescape') as cert_file:
                        cert = cert_file.read()
                    try:
                        for pem in extract_pem_certs(cert):
                            b_der = ssl.PEM_cert_to_DER_cert(pem)
                            cadata[b_der] = None
                    except Exception:
                        continue
                except OSError:
                    pass

    # paths_checked isn't used any more, but is kept just for ease of debugging
    return bytearray().join(cadata), list(paths_checked)