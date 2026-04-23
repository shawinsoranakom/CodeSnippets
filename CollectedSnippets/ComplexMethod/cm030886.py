def collect_ssl(info_add):
    import os
    try:
        import ssl
    except ImportError:
        return
    try:
        import _ssl
    except ImportError:
        _ssl = None

    def format_attr(attr, value):
        if attr.startswith('OP_'):
            return '%#8x' % value
        else:
            return value

    attributes = (
        'OPENSSL_VERSION',
        'OPENSSL_VERSION_INFO',
        'HAS_SNI',
        'OP_ALL',
        'OP_NO_TLSv1_1',
    )
    copy_attributes(info_add, ssl, 'ssl.%s', attributes, formatter=format_attr)

    for name, ctx in (
        ('SSLContext', ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)),
        ('default_https_context', ssl._create_default_https_context()),
        ('stdlib_context', ssl._create_stdlib_context()),
    ):
        attributes = (
            'minimum_version',
            'maximum_version',
            'protocol',
            'options',
            'verify_mode',
        )
        copy_attributes(info_add, ctx, f'ssl.{name}.%s', attributes)

    env_names = ["OPENSSL_CONF", "SSLKEYLOGFILE"]
    if _ssl is not None and hasattr(_ssl, 'get_default_verify_paths'):
        parts = _ssl.get_default_verify_paths()
        env_names.extend((parts[0], parts[2]))

    for name in env_names:
        try:
            value = os.environ[name]
        except KeyError:
            continue
        info_add('ssl.environ[%s]' % name, value)