async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: TradfriConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up a Tradfri config entry."""
    gateway_id = config_entry.data[CONF_GATEWAY_ID]
    tradfri_data = config_entry.runtime_data
    api = tradfri_data.api

    entities: list[TradfriSensor] = []

    for device_coordinator in tradfri_data.coordinator_list:
        if (
            not device_coordinator.device.has_light_control
            and not device_coordinator.device.has_socket_control
            and not device_coordinator.device.has_signal_repeater_control
            and not device_coordinator.device.has_air_purifier_control
        ):
            descriptions = SENSOR_DESCRIPTIONS_BATTERY
        elif device_coordinator.device.has_air_purifier_control:
            descriptions = SENSOR_DESCRIPTIONS_FAN
        else:
            continue

        for description in descriptions:
            # Added in Home assistant 2022.3
            _migrate_old_unique_ids(
                hass=hass,
                old_unique_id=f"{gateway_id}-{device_coordinator.device.id}",
                key=description.key,
            )

            entities.append(
                TradfriSensor(
                    device_coordinator,
                    api,
                    gateway_id,
                    description=description,
                )
            )

    async_add_entities(entities)