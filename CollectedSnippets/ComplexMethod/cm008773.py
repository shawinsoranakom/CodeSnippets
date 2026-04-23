def make_ssl_context(
    verify=True,
    client_certificate=None,
    client_certificate_key=None,
    client_certificate_password=None,
    legacy_support=False,
    use_certifi=True,
):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = verify
    context.verify_mode = ssl.CERT_REQUIRED if verify else ssl.CERT_NONE
    # OpenSSL 1.1.1+ Python 3.8+ keylog file
    if hasattr(context, 'keylog_filename'):
        context.keylog_filename = os.environ.get('SSLKEYLOGFILE') or None

    # Some servers may reject requests if ALPN extension is not sent. See:
    # https://github.com/python/cpython/issues/85140
    # https://github.com/yt-dlp/yt-dlp/issues/3878
    with contextlib.suppress(NotImplementedError):
        context.set_alpn_protocols(['http/1.1'])
    if verify:
        ssl_load_certs(context, use_certifi)

    if legacy_support:
        context.options |= 4  # SSL_OP_LEGACY_SERVER_CONNECT
        context.set_ciphers('DEFAULT')  # compat

    elif ssl.OPENSSL_VERSION_INFO >= (1, 1, 1) and not ssl.OPENSSL_VERSION.startswith('LibreSSL'):
        # Use the default SSL ciphers and minimum TLS version settings from Python 3.10 [1].
        # This is to ensure consistent behavior across Python versions and libraries, and help avoid fingerprinting
        # in some situations [2][3].
        # Python 3.10 only supports OpenSSL 1.1.1+ [4]. Because this change is likely
        # untested on older versions, we only apply this to OpenSSL 1.1.1+ to be safe.
        # LibreSSL is excluded until further investigation due to cipher support issues [5][6].
        # 1. https://github.com/python/cpython/commit/e983252b516edb15d4338b0a47631b59ef1e2536
        # 2. https://github.com/yt-dlp/yt-dlp/issues/4627
        # 3. https://github.com/yt-dlp/yt-dlp/pull/5294
        # 4. https://peps.python.org/pep-0644/
        # 5. https://peps.python.org/pep-0644/#libressl-support
        # 6. https://github.com/yt-dlp/yt-dlp/commit/5b9f253fa0aee996cf1ed30185d4b502e00609c4#commitcomment-89054368
        context.set_ciphers(
            '@SECLEVEL=2:ECDH+AESGCM:ECDH+CHACHA20:ECDH+AES:DHE+AES:!aNULL:!eNULL:!aDSS:!SHA1:!AESCCM')
        context.minimum_version = ssl.TLSVersion.TLSv1_2

    if client_certificate:
        try:
            context.load_cert_chain(
                client_certificate, keyfile=client_certificate_key,
                password=client_certificate_password)
        except ssl.SSLError:
            raise RequestError('Unable to load client certificate')

        if getattr(context, 'post_handshake_auth', None) is not None:
            context.post_handshake_auth = True
    return context