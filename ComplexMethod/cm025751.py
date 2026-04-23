def _add_remove_devices() -> None:
        """Handle additions of devices and sensors."""

        entities: list[SensiboMotionSensor | SensiboDeviceSensor] = []
        nonlocal added_devices
        new_devices, _, new_added_devices = coordinator.get_devices(added_devices)
        added_devices = new_added_devices

        if new_devices:
            entities.extend(
                SensiboMotionSensor(
                    coordinator, device_id, sensor_id, sensor_data, description
                )
                for device_id, device_data in coordinator.data.parsed.items()
                if device_data.motion_sensors
                for sensor_id, sensor_data in device_data.motion_sensors.items()
                if sensor_id in new_devices
                for description in MOTION_SENSOR_TYPES
            )
            entities.extend(
                SensiboDeviceSensor(coordinator, device_id, description)
                for device_id, device_data in coordinator.data.parsed.items()
                if device_id in new_devices
                for description in DESCRIPTION_BY_MODELS.get(
                    device_data.model, DEVICE_SENSOR_TYPES
                )
            )
            async_add_entities(entities)