async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: EcovacsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add entities for passed config_entry in HA."""
    controller = config_entry.runtime_data

    entities: list[EcovacsEntity] = get_supported_entities(
        controller, EcovacsSensor, ENTITY_DESCRIPTIONS
    )
    entities.extend(
        EcovacsLifespanSensor(device, device.capabilities.life_span, description)
        for device in controller.devices
        for description in LIFESPAN_ENTITY_DESCRIPTIONS
        if description.component in device.capabilities.life_span.types
    )
    entities.extend(
        EcovacsErrorSensor(device, capability)
        for device in controller.devices
        if (capability := device.capabilities.error)
    )

    async_add_entities(entities)

    async def _add_legacy_lifespan_entities() -> None:
        entities = []
        for device in controller.legacy_devices:
            for description in LEGACY_LIFESPAN_SENSORS:
                if (
                    description.component in device.components
                    and not controller.legacy_entity_is_added(
                        device, description.component
                    )
                ):
                    controller.add_legacy_entity(device, description.component)
                    entities.append(EcovacsLegacyLifespanSensor(device, description))

        if entities:
            async_add_entities(entities)

    def _fire_ecovacs_legacy_lifespan_event(_: Any) -> None:
        hass.create_task(_add_legacy_lifespan_entities())

    legacy_entities = []
    for device in controller.legacy_devices:
        config_entry.async_on_unload(
            device.lifespanEvents.subscribe(
                _fire_ecovacs_legacy_lifespan_event
            ).unsubscribe
        )
        if not controller.legacy_entity_is_added(device, "battery_status"):
            controller.add_legacy_entity(device, "battery_status")
            legacy_entities.append(EcovacsLegacyBatterySensor(device))

    if legacy_entities:
        async_add_entities(legacy_entities)