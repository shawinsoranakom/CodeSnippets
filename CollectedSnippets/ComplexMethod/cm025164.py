async def async_prepare_setup_platform(
    hass: core.HomeAssistant, hass_config: ConfigType, domain: str, platform_name: str
) -> ModuleType | None:
    """Load a platform and makes sure dependencies are setup.

    This method is a coroutine.
    """
    platform_path = PLATFORM_FORMAT.format(domain=domain, platform=platform_name)

    def log_error(msg: str) -> None:
        """Log helper."""

        _LOGGER.error(
            "Unable to prepare setup for platform '%s': %s", platform_path, msg
        )
        async_notify_setup_error(hass, platform_path)

    try:
        integration = await loader.async_get_integration(hass, platform_name)
    except loader.IntegrationNotFound:
        log_error("Integration not found")
        return None

    # Platforms cannot exist on their own, they are part of their integration.
    # If the integration is not set up yet, and can be set up, set it up.
    #
    # We do this before we import the platform so the platform already knows
    # where the top level component is.
    #
    if load_top_level_component := integration.domain not in hass.config.components:
        # Process deps and reqs as soon as possible, so that requirements are
        # available when we import the platform. We only do this if the integration
        # is not in hass.config.components yet, as we already processed them in
        # async_setup_component if it is.
        try:
            await async_process_deps_reqs(hass, hass_config, integration)
        except HomeAssistantError as err:
            log_error(str(err))
            return None

        try:
            component = await integration.async_get_component()
        except ImportError as exc:
            log_error(f"Unable to import the component ({exc}).")
            return None

    if not integration.platforms_exists((domain,)):
        log_error(
            f"Platform not found (No module named '{integration.pkg_path}.{domain}')"
        )
        return None

    try:
        platform = await integration.async_get_platform(domain)
    except ImportError as exc:
        log_error(f"Platform not found ({exc}).")
        return None

    # Already loaded
    if platform_path in hass.config.components:
        return platform

    # Platforms cannot exist on their own, they are part of their integration.
    # If the integration is not set up yet, and can be set up, set it up.
    if load_top_level_component:
        if (
            hasattr(component, "setup") or hasattr(component, "async_setup")
        ) and not await async_setup_component(hass, integration.domain, hass_config):
            log_error("Unable to set up component.")
            return None

    return platform