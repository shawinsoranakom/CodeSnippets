def async_get_issue_tracker(
    hass: HomeAssistant | None,
    *,
    integration: Integration | None = None,
    integration_domain: str | None = None,
    module: str | None = None,
) -> str | None:
    """Return a URL for an integration's issue tracker."""
    issue_tracker = (
        "https://github.com/home-assistant/core/issues?q=is%3Aopen+is%3Aissue"
    )
    if not integration and not integration_domain and not module:
        # If we know nothing about the integration, suggest opening an issue on HA core
        return issue_tracker

    if module and not integration_domain:
        # If we only have a module, we can try to get the integration domain from it
        if module.startswith("custom_components."):
            integration_domain = module.split(".")[1]
        elif module.startswith("homeassistant.components."):
            integration_domain = module.split(".")[2]

    if not integration:
        integration = async_get_issue_integration(hass, integration_domain)

    if integration and not integration.is_built_in:
        return integration.issue_tracker

    if module and "custom_components" in module:
        return None

    if integration:
        integration_domain = integration.domain

    if integration_domain:
        issue_tracker += f"+label%3A%22integration%3A+{integration_domain}%22"
    return issue_tracker