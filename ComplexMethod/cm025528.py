async def async_provide_implementation(
    hass: HomeAssistant, domain: str
) -> list[config_entry_oauth2_flow.AbstractOAuth2Implementation]:
    """Provide an implementation for a domain."""
    services = await _get_services(hass)

    for service in services:
        if (
            service["service"] == domain
            and service["min_version"] <= CURRENT_PLAIN_VERSION
            and (
                service.get("accepts_new_authorizations", True)
                or (
                    (entries := hass.config_entries.async_entries(domain))
                    and any(
                        entry.data.get("auth_implementation") == DOMAIN
                        for entry in entries
                    )
                )
            )
        ):
            return [CloudOAuth2Implementation(hass, domain)]

    return []