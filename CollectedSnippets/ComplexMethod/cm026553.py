async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: NutConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the NUT switches."""
    pynut_data = config_entry.runtime_data
    coordinator = pynut_data.coordinator
    status = coordinator.data

    # Dynamically add outlet switch types
    if (num_outlets := status.get("outlet.count")) is None:
        return

    data = pynut_data.data
    unique_id = pynut_data.unique_id
    user_available_commands = pynut_data.user_available_commands
    switch_descriptions = [
        SwitchEntityDescription(
            key=f"outlet.{outlet_num!s}.load.poweronoff",
            translation_key="outlet_number_load_poweronoff",
            translation_placeholders={
                "outlet_name": status.get(f"outlet.{outlet_num!s}.name")
                or str(outlet_num)
            },
            device_class=SwitchDeviceClass.OUTLET,
            entity_registry_enabled_default=True,
        )
        for outlet_num in range(1, int(num_outlets) + 1)
        if (
            status.get(f"outlet.{outlet_num!s}.switchable") == "yes"
            and f"outlet.{outlet_num!s}.load.on" in user_available_commands
            and f"outlet.{outlet_num!s}.load.off" in user_available_commands
        )
    ]

    async_add_entities(
        NUTSwitch(coordinator, description, data, unique_id)
        for description in switch_descriptions
    )