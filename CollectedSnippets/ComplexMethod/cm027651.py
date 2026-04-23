def _get_external_url(
    hass: HomeAssistant,
    *,
    allow_cloud: bool = True,
    allow_ip: bool = True,
    prefer_cloud: bool = False,
    require_current_request: bool = False,
    require_ssl: bool = False,
    require_standard_port: bool = False,
    require_cloud: bool = False,
) -> str:
    """Get external URL of this instance."""
    if require_cloud:
        return _get_cloud_url(hass, require_current_request=require_current_request)

    if prefer_cloud and allow_cloud:
        with suppress(NoURLAvailableError):
            return _get_cloud_url(hass)

    if hass.config.external_url:
        external_url = yarl.URL(hass.config.external_url)
        if (
            (allow_ip or not is_ip_address(str(external_url.host)))
            and (
                not require_current_request or external_url.host == _get_request_host()
            )
            and (not require_standard_port or external_url.is_default_port())
            and (
                not require_ssl
                or (
                    external_url.scheme == "https"
                    and not is_ip_address(str(external_url.host))
                )
            )
        ):
            return normalize_url(str(external_url))

    if allow_cloud:
        with suppress(NoURLAvailableError):
            return _get_cloud_url(hass, require_current_request=require_current_request)

    raise NoURLAvailableError