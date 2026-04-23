def _report_usage_integration_domain(
    hass: HomeAssistant | None,
    what: str,
    breaks_in_ha_version: str | None,
    integration: Integration,
    core_integration_behavior: ReportBehavior,
    custom_integration_behavior: ReportBehavior,
    level: int,
) -> None:
    """Report incorrect usage in an integration (identified via domain).

    Async friendly.
    """
    integration_behavior = core_integration_behavior
    if not integration.is_built_in:
        integration_behavior = custom_integration_behavior

    if integration_behavior is ReportBehavior.IGNORE:
        return

    # Keep track of integrations already reported to prevent flooding
    key = f"{integration.domain}:{what}"
    if (
        integration_behavior is not ReportBehavior.ERROR
        and key in _REPORTED_INTEGRATIONS
    ):
        return
    _REPORTED_INTEGRATIONS.add(key)

    report_issue = async_suggest_report_issue(hass, integration=integration)
    integration_type = "" if integration.is_built_in else "custom "
    _LOGGER.log(
        level,
        "Detected that %sintegration '%s' %s. %s %s",
        integration_type,
        integration.domain,
        what,
        f"This will stop working in Home Assistant {breaks_in_ha_version}, please"
        if breaks_in_ha_version
        else "Please",
        report_issue,
    )

    if integration_behavior is ReportBehavior.ERROR:
        raise RuntimeError(
            f"Detected that {integration_type}integration "
            f"'{integration.domain}' {what}. Please {report_issue}"
        )