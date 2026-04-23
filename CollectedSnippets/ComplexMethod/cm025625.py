async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: EnphaseConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Enphase Envoy select platform."""
    coordinator = config_entry.runtime_data
    envoy_data = coordinator.envoy.data
    assert envoy_data is not None
    entities: list[SelectEntity] = []
    if envoy_data.dry_contact_settings:
        entities.extend(
            EnvoyRelaySelectEntity(coordinator, entity, relay)
            for entity in RELAY_ENTITIES
            for relay in envoy_data.dry_contact_settings
        )
    if (
        envoy_data.tariff
        and envoy_data.tariff.storage_settings
        and coordinator.envoy.supported_features & SupportedFeatures.ENCHARGE
    ):
        entities.append(
            EnvoyStorageSettingsSelectEntity(coordinator, STORAGE_MODE_ENTITY)
        )
    async_add_entities(entities)