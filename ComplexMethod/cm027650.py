def _get_internal_url(
    hass: HomeAssistant,
    *,
    allow_ip: bool = True,
    require_current_request: bool = False,
    require_ssl: bool = False,
    require_standard_port: bool = False,
) -> str:
    """Get internal URL of this instance."""
    if hass.config.internal_url:
        internal_url = yarl.URL(hass.config.internal_url)
        if (
            (not require_current_request or internal_url.host == _get_request_host())
            and (not require_ssl or internal_url.scheme == "https")
            and (not require_standard_port or internal_url.is_default_port())
            and (allow_ip or not is_ip_address(str(internal_url.host)))
        ):
            return normalize_url(str(internal_url))

    # Fallback to detected local IP
    if allow_ip and not (
        require_ssl or hass.config.api is None or hass.config.api.use_ssl
    ):
        ip_url = yarl.URL.build(
            scheme="http", host=hass.config.api.local_ip, port=hass.config.api.port
        )
        if (
            ip_url.host
            and not is_loopback(ip_address(ip_url.host))
            and (not require_current_request or ip_url.host == _get_request_host())
            and (not require_standard_port or ip_url.is_default_port())
        ):
            return normalize_url(str(ip_url))

    raise NoURLAvailableError