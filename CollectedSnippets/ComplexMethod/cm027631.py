async def _async_process_integration_platforms(
    hass: HomeAssistant,
    platform_name: str,
    top_level_components: set[str],
    process_job: HassJob,
) -> None:
    """Process integration platforms for a component."""
    integrations = await async_get_integrations(hass, top_level_components)
    loaded_integrations: list[Integration] = [
        integration
        for integration in integrations.values()
        if not isinstance(integration, Exception)
    ]
    # Finally, fetch the platforms for each integration and process them.
    # This uses the import executor in a loop. If there are a lot
    # of integration with the integration platform to process,
    # this could be a bottleneck.
    futures: list[asyncio.Future[None]] = []
    for integration in loaded_integrations:
        if not integration.platforms_exists((platform_name,)):
            continue
        try:
            platform = await integration.async_get_platform(platform_name)
        except ImportError:
            _LOGGER.debug(
                "Unexpected error importing %s for %s",
                platform_name,
                integration.domain,
            )
            continue

        if future := hass.async_run_hass_job(
            process_job, hass, integration.domain, platform
        ):
            futures.append(future)

    if futures:
        await asyncio.gather(*futures)