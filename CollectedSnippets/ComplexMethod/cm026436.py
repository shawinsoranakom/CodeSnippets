async def _process_config(hass: HomeAssistant, hass_config: ConfigType) -> None:
    """Process config."""
    coordinators = hass.data.pop(DATA_COORDINATORS, None)

    # Remove old ones
    if coordinators:
        for coordinator in coordinators:
            coordinator.async_remove()

    async def init_coordinator(
        hass: HomeAssistant, conf_section: dict[str, Any]
    ) -> TriggerUpdateCoordinator:
        coordinator = TriggerUpdateCoordinator(hass, conf_section)
        await coordinator.async_setup(hass_config)
        return coordinator

    coordinator_tasks: list[Coroutine[Any, Any, TriggerUpdateCoordinator]] = []

    for conf_section in hass_config[DOMAIN]:
        if CONF_TRIGGERS in conf_section:
            coordinator_tasks.append(init_coordinator(hass, conf_section))
            continue

        for platform_domain in PLATFORMS:
            if platform_domain in conf_section:
                hass.async_create_task(
                    discovery.async_load_platform(
                        hass,
                        platform_domain,
                        DOMAIN,
                        {
                            "unique_id": conf_section.get(CONF_UNIQUE_ID),
                            "entities": [
                                {
                                    **entity_conf,
                                    "raw_blueprint_inputs": conf_section.raw_blueprint_inputs,
                                    "raw_configs": conf_section.raw_config,
                                }
                                for entity_conf in conf_section[platform_domain]
                            ],
                        },
                        hass_config,
                    ),
                    eager_start=True,
                )

    if coordinator_tasks:
        hass.data[DATA_COORDINATORS] = await asyncio.gather(*coordinator_tasks)