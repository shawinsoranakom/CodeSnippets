async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ShellyConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up button entities."""
    entry_data = config_entry.runtime_data
    coordinator: ShellyRpcCoordinator | ShellyBlockCoordinator | None
    device_gen = get_device_entry_gen(config_entry)
    if device_gen in RPC_GENERATIONS:
        coordinator = entry_data.rpc
    else:
        coordinator = entry_data.block

    if TYPE_CHECKING:
        assert coordinator is not None

    if coordinator.device.initialized:
        await er.async_migrate_entries(
            hass, config_entry.entry_id, partial(async_migrate_unique_ids, coordinator)
        )

    # Remove the 'restart' button for sleeping devices as it was mistakenly
    # added in https://github.com/home-assistant/core/pull/154673
    entry_sleep_period = config_entry.data[CONF_SLEEP_PERIOD]
    if device_gen in RPC_GENERATIONS and entry_sleep_period:
        async_remove_shelly_entity(hass, BUTTON_DOMAIN, f"{coordinator.mac}-reboot")

    entities: list[ShellyButton] = []

    entities.extend(
        ShellyButton(coordinator, button)
        for button in BUTTONS
        if button.supported(coordinator)
    )

    async_add_entities(entities)

    if not isinstance(coordinator, ShellyRpcCoordinator):
        return

    # add RPC buttons
    if entry_sleep_period:
        async_setup_entry_rpc(
            hass,
            config_entry,
            async_add_entities,
            RPC_BUTTONS,
            RpcSleepingSmokeMuteButton,
        )
    else:
        async_setup_entry_rpc(
            hass, config_entry, async_add_entities, RPC_BUTTONS, RpcVirtualButton
        )

        # the user can remove virtual components from the device configuration, so
        # we need to remove orphaned entities
        virtual_button_component_ids = get_virtual_component_ids(
            coordinator.device.config, BUTTON_DOMAIN
        )
        async_remove_orphaned_entities(
            hass,
            config_entry.entry_id,
            coordinator.mac,
            BUTTON_DOMAIN,
            virtual_button_component_ids,
        )