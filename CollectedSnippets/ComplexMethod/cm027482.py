def _check_device() -> None:
        current_devices = set(coordinator.data)
        new_devices = current_devices - known_devices
        if new_devices:
            known_devices.update(new_devices)
            sensors_list = [
                AmazonSensorEntity(coordinator, serial_num, sensor_desc)
                for sensor_desc in SENSORS
                for serial_num in new_devices
                if coordinator.data[serial_num].sensors.get(sensor_desc.key) is not None
            ]
            notifications_list = [
                AmazonSensorEntity(coordinator, serial_num, notification_desc)
                for notification_desc in NOTIFICATIONS
                for serial_num in new_devices
                if coordinator.data[serial_num].notifications_supported
            ]
            async_add_entities(sensors_list + notifications_list)