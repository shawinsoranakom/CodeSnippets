def get_external_ip() -> Optional[str]:
    """Get the *external* IP address of the current machine.

    Returns
    -------
    string
        The external IPv4 address of the current machine.

    """
    global _external_ip

    if _external_ip is not None:
        return _external_ip

    response = _make_blocking_http_get(_AWS_CHECK_IP, timeout=5)

    if _looks_like_an_ip_adress(response):
        _external_ip = response
    else:
        LOGGER.warning(
            # fmt: off
            "Did not auto detect external IP.\n"
            "Please go to %s for debugging hints.",
            # fmt: on
            util.HELP_DOC
        )
        _external_ip = None

    return _external_ip