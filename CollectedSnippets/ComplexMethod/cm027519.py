async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle config entry migration."""

    if entry.version < 3:
        # We keep the old data around, so we can use that to clean up the webhook in the future
        hass.config_entries.async_update_entry(
            entry, version=3, data={OLD_DATA: dict(entry.data)}
        )

    if entry.minor_version < 2:

        def migrate_entities(entity_entry: RegistryEntry) -> dict[str, Any] | None:
            if entity_entry.domain == "binary_sensor":
                device_id, attribute = entity_entry.unique_id.split(".")
                if (
                    capability := BINARY_SENSOR_ATTRIBUTES_TO_CAPABILITIES.get(
                        attribute
                    )
                ) is None:
                    return None
                new_unique_id = (
                    f"{device_id}_{MAIN}_{capability}_{attribute}_{attribute}"
                )
                return {
                    "new_unique_id": new_unique_id,
                }
            if entity_entry.domain in {"cover", "climate", "fan", "light", "lock"}:
                return {"new_unique_id": f"{entity_entry.unique_id}_{MAIN}"}
            if entity_entry.domain == "sensor":
                delimiter = "." if " " not in entity_entry.unique_id else " "
                if delimiter not in entity_entry.unique_id:
                    return None
                device_id, attribute = entity_entry.unique_id.split(
                    delimiter, maxsplit=1
                )
                if (
                    capability := SENSOR_ATTRIBUTES_TO_CAPABILITIES.get(attribute)
                ) is None:
                    if attribute in {
                        "energy_meter",
                        "power_meter",
                        "deltaEnergy_meter",
                        "powerEnergy_meter",
                        "energySaved_meter",
                    }:
                        return {
                            "new_unique_id": f"{device_id}_{MAIN}_{Capability.POWER_CONSUMPTION_REPORT}_{Attribute.POWER_CONSUMPTION}_{attribute}",
                        }
                    if attribute in {
                        "X Coordinate",
                        "Y Coordinate",
                        "Z Coordinate",
                    }:
                        new_attribute = {
                            "X Coordinate": "x_coordinate",
                            "Y Coordinate": "y_coordinate",
                            "Z Coordinate": "z_coordinate",
                        }[attribute]
                        return {
                            "new_unique_id": f"{device_id}_{MAIN}_{Capability.THREE_AXIS}_{Attribute.THREE_AXIS}_{new_attribute}",
                        }
                    if attribute in {
                        Attribute.MACHINE_STATE,
                        Attribute.COMPLETION_TIME,
                    }:
                        capability = determine_machine_type(
                            hass, entry.entry_id, device_id
                        )
                        if capability is None:
                            return None
                        return {
                            "new_unique_id": f"{device_id}_{MAIN}_{capability}_{attribute}_{attribute}",
                        }
                    return None
                return {
                    "new_unique_id": f"{device_id}_{MAIN}_{capability}_{attribute}_{attribute}",
                }

            if entity_entry.domain == "switch":
                return {
                    "new_unique_id": f"{entity_entry.unique_id}_{MAIN}_{Capability.SWITCH}_{Attribute.SWITCH}_{Attribute.SWITCH}",
                }

            return None

        await async_migrate_entries(hass, entry.entry_id, migrate_entities)
        hass.config_entries.async_update_entry(
            entry,
            minor_version=2,
        )

    if entry.minor_version < 3:
        data = deepcopy(dict(entry.data))
        old_data: dict[str, Any] | None = data.pop(OLD_DATA, None)
        if old_data is not None:
            _LOGGER.info("Found old data during migration")
            client = SmartThings(session=async_get_clientsession(hass))
            access_token = old_data[CONF_ACCESS_TOKEN]
            installed_app_id = old_data[CONF_INSTALLED_APP_ID]
            try:
                app = await client.get_installed_app(access_token, installed_app_id)
                _LOGGER.info("Found old app %s, named %s", app.app_id, app.display_name)
                await client.delete_installed_app(access_token, installed_app_id)
                await client.delete_smart_app(access_token, app.app_id)
            except SmartThingsError as err:
                _LOGGER.warning(
                    "Could not clean up old smart app during migration: %s", err
                )
            else:
                _LOGGER.info("Successfully cleaned up old smart app during migration")
            if CONF_TOKEN not in data:
                data[OLD_DATA] = {CONF_LOCATION_ID: old_data[CONF_LOCATION_ID]}
        hass.config_entries.async_update_entry(
            entry,
            data=data,
            minor_version=3,
        )

    return True