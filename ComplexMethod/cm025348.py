def _async_setup_rpc_entry(
    hass: HomeAssistant,
    config_entry: ShellyConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up entities for RPC device."""
    entities: list[ShellyRpcEvent | ShellyRpcScriptEvent] = []

    coordinator = config_entry.runtime_data.rpc
    if TYPE_CHECKING:
        assert coordinator

    key_instances = get_rpc_key_instances(coordinator.device.status, RPC_EVENT.key)

    for key in key_instances:
        if RPC_EVENT.removal_condition and RPC_EVENT.removal_condition(
            coordinator.device.config, coordinator.device.status, key
        ):
            unique_id = f"{coordinator.mac}-{key}"
            async_remove_shelly_entity(hass, EVENT_DOMAIN, unique_id)
        else:
            entities.append(ShellyRpcEvent(coordinator, key, RPC_EVENT))

    script_instances = get_rpc_key_instances(
        coordinator.device.status, SCRIPT_EVENT.key
    )
    script_events = config_entry.runtime_data.rpc_script_events
    for script in script_instances:
        if get_rpc_custom_name(coordinator.device, script) == BLE_SCRIPT_NAME:
            continue

        if script_events and (event_types := script_events[get_rpc_key_id(script)]):
            entities.append(
                ShellyRpcScriptEvent(coordinator, script, SCRIPT_EVENT, event_types)
            )

    # If a script is removed, from the device configuration, we need to remove orphaned entities
    async_remove_orphaned_entities(
        hass,
        config_entry.entry_id,
        coordinator.mac,
        EVENT_DOMAIN,
        coordinator.device.status,
        "script",
    )

    async_add_entities(entities)