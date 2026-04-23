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