def _get_custom_components(hass: HomeAssistant) -> dict[str, Integration]:
    """Return list of custom integrations."""
    if hass.config.recovery_mode or hass.config.safe_mode:
        return {}

    try:
        import custom_components  # noqa: PLC0415
    except ImportError:
        return {}

    dirs = [
        entry
        for path in custom_components.__path__
        for entry in pathlib.Path(path).iterdir()
        if entry.is_dir()
    ]

    integrations = _resolve_integrations_from_root(
        hass,
        custom_components,
        [comp.name for comp in dirs],
    )
    return {
        integration.domain: integration
        for integration in integrations.values()
        if integration is not None
    }