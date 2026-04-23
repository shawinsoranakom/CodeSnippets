def has_tls_version(version):
    """Check if a TLS/SSL version is enabled

    :param version: TLS version name or ssl.TLSVersion member
    :return: bool
    """
    if isinstance(version, str):
        version = ssl.TLSVersion.__members__[version]

    # check compile time flags like ssl.HAS_TLSv1_2
    if not getattr(ssl, f'HAS_{version.name}'):
        return False

    if IS_OPENSSL_3_0_0 and version < ssl.TLSVersion.TLSv1_2:
        # bpo43791: 3.0.0-alpha14 fails with TLSV1_ALERT_INTERNAL_ERROR
        return False

    # check runtime and dynamic crypto policy settings. A TLS version may
    # be compiled in but disabled by a policy or config option.
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    if (
            hasattr(ctx, 'minimum_version') and
            ctx.minimum_version != ssl.TLSVersion.MINIMUM_SUPPORTED and
            version < ctx.minimum_version
    ):
        return False
    if (
        hasattr(ctx, 'maximum_version') and
        ctx.maximum_version != ssl.TLSVersion.MAXIMUM_SUPPORTED and
        version > ctx.maximum_version
    ):
        return False

    return True