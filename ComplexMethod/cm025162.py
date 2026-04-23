async def _async_process_dependencies(
    hass: core.HomeAssistant, config: ConfigType, integration: loader.Integration
) -> list[str]:
    """Ensure all dependencies are set up.

    Returns a list of dependencies which failed to set up.
    """
    setup_futures = hass.data.setdefault(_DATA_SETUP, {})

    dependencies_tasks: dict[str, asyncio.Future[bool]] = {}

    for dep in integration.dependencies:
        fut = setup_futures.get(dep)
        if fut is None:
            if dep in hass.config.components:
                continue
            fut = create_eager_task(
                async_setup_component(hass, dep, config),
                name=f"setup {dep} as dependency of {integration.domain}",
                loop=hass.loop,
            )
        dependencies_tasks[dep] = fut

    to_be_loaded = hass.data.get(_DATA_SETUP_DONE, {})
    # We don't want to just wait for the futures from `to_be_loaded` here.
    # We want to ensure that our after_dependencies are always actually
    # scheduled to be set up, as if for whatever reason they had not been,
    # we would deadlock waiting for them here.
    for dep in integration.after_dependencies:
        if dep not in to_be_loaded or dep in dependencies_tasks:
            continue
        fut = setup_futures.get(dep)
        if fut is None:
            if dep in hass.config.components:
                continue
            fut = create_eager_task(
                async_setup_component(hass, dep, config),
                name=f"setup {dep} as after dependency of {integration.domain}",
                loop=hass.loop,
            )
        dependencies_tasks[dep] = fut

    if not dependencies_tasks:
        return []

    if dependencies_tasks:
        _LOGGER.debug(
            "Dependency %s will wait for dependencies %s",
            integration.domain,
            dependencies_tasks.keys(),
        )

    async with hass.timeout.async_freeze(integration.domain):
        results = await asyncio.gather(*dependencies_tasks.values())

    failed = [
        domain for idx, domain in enumerate(dependencies_tasks) if not results[idx]
    ]

    if failed:
        _LOGGER.error(
            "Unable to set up dependencies of '%s'. Setup failed for dependencies: %s",
            integration.domain,
            failed,
        )

    return failed