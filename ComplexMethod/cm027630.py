def _async_integration_platform_component_loaded(
    hass: HomeAssistant,
    integration_platforms: list[IntegrationPlatform],
    event: Event[EventComponentLoaded],
) -> None:
    """Process integration platforms for a component."""
    if "." in (component_name := event.data[ATTR_COMPONENT]):
        return

    integration = async_get_loaded_integration(hass, component_name)
    # First filter out platforms that the integration already processed.
    integration_platforms_by_name: dict[str, IntegrationPlatform] = {}
    for integration_platform in integration_platforms:
        if component_name in integration_platform.seen_components:
            continue
        integration_platform.seen_components.add(component_name)
        integration_platforms_by_name[integration_platform.platform_name] = (
            integration_platform
        )

    if not integration_platforms_by_name:
        return

    # Next, check which platforms exist for this integration.
    platforms_that_exist = integration.platforms_exists(integration_platforms_by_name)
    if not platforms_that_exist:
        return

    # If everything is already loaded, we can avoid creating a task.
    can_use_cache = True
    platforms: dict[str, ModuleType] = {}
    for platform_name in platforms_that_exist:
        if platform := integration.get_platform_cached(platform_name):
            platforms[platform_name] = platform
        else:
            can_use_cache = False
            break

    if can_use_cache:
        _process_integration_platforms(
            hass,
            integration,
            platforms,
            integration_platforms_by_name,
        )
        return

    # At least one of the platforms is not loaded, we need to load them
    # so we have to fall back to creating a task.
    hass.async_create_task_internal(
        _async_process_integration_platforms_for_component(
            hass, integration, platforms_that_exist, integration_platforms_by_name
        ),
        eager_start=True,
    )