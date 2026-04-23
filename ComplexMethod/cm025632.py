async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: EnphaseConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Enphase Envoy switch platform."""
    coordinator = config_entry.runtime_data
    envoy_data = coordinator.envoy.data
    assert envoy_data is not None
    entities: list[SwitchEntity] = []
    if envoy_data.enpower:
        entities.extend(
            [
                EnvoyEnpowerSwitchEntity(
                    coordinator, ENPOWER_GRID_SWITCH, envoy_data.enpower
                )
            ]
        )

    if envoy_data.dry_contact_status:
        entities.extend(
            EnvoyDryContactSwitchEntity(coordinator, RELAY_STATE_SWITCH, relay)
            for relay in envoy_data.dry_contact_status
        )

    if (
        envoy_data.tariff
        and envoy_data.tariff.storage_settings
        and (coordinator.envoy.supported_features & SupportedFeatures.ENCHARGE)
    ):
        entities.append(
            EnvoyStorageSettingsSwitchEntity(
                coordinator, CHARGE_FROM_GRID_SWITCH, envoy_data.enpower
            )
        )

    async_add_entities(entities)