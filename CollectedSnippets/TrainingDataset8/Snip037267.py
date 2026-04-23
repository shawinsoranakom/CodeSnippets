def _server_cookie_secret() -> str:
    """Symmetric key used to produce signed cookies. If deploying on multiple replicas, this should
    be set to the same value across all replicas to ensure they all share the same secret.

    Default: randomly generated secret key.
    """
    return secrets.token_hex()