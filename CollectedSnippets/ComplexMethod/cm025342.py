def _async_setup_rpc_entry(
    hass: HomeAssistant,
    config_entry: ShellyConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up entities for RPC device."""
    coordinator = config_entry.runtime_data.rpc
    assert coordinator
    climate_key_ids = get_rpc_key_ids(coordinator.device.status, "thermostat")
    blutrv_key_ids = get_rpc_key_ids(coordinator.device.status, BLU_TRV_IDENTIFIER)

    climate_ids = []
    for id_ in climate_key_ids:
        climate_ids.append(id_)
        # There are three configuration scenarios for WallDisplay:
        # - relay mode (no thermostat)
        # - thermostat mode using the internal relay as an actuator
        # - thermostat mode using an external (from another device) relay as
        #   an actuator
        if is_rpc_thermostat_internal_actuator(coordinator.device.status):
            # Wall Display relay is used as the thermostat actuator,
            # we need to remove a switch entity
            unique_id = f"{coordinator.mac}-switch:{id_}"
            async_remove_shelly_entity(hass, "switch", unique_id)

    if climate_ids:
        async_add_entities(RpcClimate(coordinator, id_) for id_ in climate_ids)

    if blutrv_key_ids:
        async_add_entities(RpcBluTrvClimate(coordinator, id_) for id_ in blutrv_key_ids)

    async_setup_entry_rpc(
        hass,
        config_entry,
        async_add_entities,
        RPC_LINKEDGO_THERMOSTAT,
        RpcLinkedgoThermostatClimate,
    )