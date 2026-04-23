def async_add_sensor(_: EventType, sensor_id: str) -> None:
        """Add sensor from deCONZ."""
        sensor = hub.api.sensors[sensor_id]
        entities: list[DeconzSensor] = []

        for description in ENTITY_DESCRIPTIONS:
            if description.instance_check and not isinstance(
                sensor, description.instance_check
            ):
                continue

            no_sensor_data = False
            if not description.supported_fn(sensor):
                no_sensor_data = True

            if description.instance_check is None:
                if (
                    sensor.type.startswith("CLIP")
                    or (no_sensor_data and description.key != "battery")
                    or (
                        (unique_id := sensor.unique_id.rpartition("-")[0])
                        in known_device_entities[description.key]
                    )
                ):
                    continue
                known_device_entities[description.key].add(unique_id)
                if no_sensor_data and description.key == "battery":
                    DeconzBatteryTracker(
                        sensor_id, hub, description, async_add_entities
                    )
                    continue

            if no_sensor_data:
                continue

            entities.append(DeconzSensor(sensor, hub, description))

        async_add_entities(entities)