def get_url(
    hass: HomeAssistant,
    *,
    require_current_request: bool = False,
    require_ssl: bool = False,
    require_standard_port: bool = False,
    require_cloud: bool = False,
    allow_internal: bool = True,
    allow_external: bool = True,
    allow_cloud: bool = True,
    allow_ip: bool | None = None,
    prefer_external: bool | None = None,
    prefer_cloud: bool = False,
) -> str:
    """Get a URL to this instance."""
    if require_current_request and http.current_request.get() is None:
        raise NoURLAvailableError

    if prefer_external is None:
        prefer_external = hass.config.api is not None and hass.config.api.use_ssl

    if allow_ip is None:
        allow_ip = hass.config.api is None or not hass.config.api.use_ssl

    order = [TYPE_URL_INTERNAL, TYPE_URL_EXTERNAL]
    if prefer_external:
        order.reverse()

    # Try finding an URL in the order specified
    for url_type in order:
        if allow_internal and url_type == TYPE_URL_INTERNAL and not require_cloud:
            with suppress(NoURLAvailableError):
                return _get_internal_url(
                    hass,
                    allow_ip=allow_ip,
                    require_current_request=require_current_request,
                    require_ssl=require_ssl,
                    require_standard_port=require_standard_port,
                )

        if require_cloud or (allow_external and url_type == TYPE_URL_EXTERNAL):
            with suppress(NoURLAvailableError):
                return _get_external_url(
                    hass,
                    allow_cloud=allow_cloud,
                    allow_ip=allow_ip,
                    prefer_cloud=prefer_cloud,
                    require_current_request=require_current_request,
                    require_ssl=require_ssl,
                    require_standard_port=require_standard_port,
                    require_cloud=require_cloud,
                )
            if require_cloud:
                raise NoURLAvailableError

    # For current request, we accept loopback interfaces (e.g., 127.0.0.1),
    # the Supervisor hostname and localhost transparently
    request_host = _get_request_host()
    if (
        require_current_request
        and request_host is not None
        and hass.config.api is not None
    ):
        scheme = "https" if hass.config.api.use_ssl else "http"
        current_url = yarl.URL.build(
            scheme=scheme, host=request_host, port=hass.config.api.port
        )

        known_hostnames = ["localhost"]
        if is_hassio(hass):
            # Local import to avoid circular dependencies
            from homeassistant.components.hassio import get_host_info  # noqa: PLC0415

            if host_info := get_host_info(hass):
                known_hostnames.extend(
                    [host_info["hostname"], f"{host_info['hostname']}.local"]
                )

        if (
            (
                (
                    allow_ip
                    and is_ip_address(request_host)
                    and is_loopback(ip_address(request_host))
                )
                or request_host in known_hostnames
            )
            and (not require_ssl or current_url.scheme == "https")
            and (not require_standard_port or current_url.is_default_port())
        ):
            return normalize_url(str(current_url))

    # We have to be honest now, we have no viable option available
    raise NoURLAvailableError