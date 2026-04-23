def _calculate_device_class(
        self, new_state: State, unit: str | None
    ) -> SensorDeviceClass | None:
        """Return the calculated device class.

        The device class is calculated based on the state characteristics,
        the source device class and the unit of measurement is
        in the device class units list.
        """

        device_class: SensorDeviceClass | None = None
        stat_type = self._state_characteristic
        if stat_type in STATS_DATETIME:
            return SensorDeviceClass.TIMESTAMP
        if stat_type in STATS_NUMERIC_RETAIN_UNIT:
            device_class = new_state.attributes.get(ATTR_DEVICE_CLASS)
            if device_class is None:
                return None
            if (
                sensor_device_class := try_parse_enum(SensorDeviceClass, device_class)
            ) is None:
                return None
            if (
                sensor_device_class
                and (
                    sensor_state_classes := DEVICE_CLASS_STATE_CLASSES.get(
                        sensor_device_class
                    )
                )
                and sensor_state_classes
                and SensorStateClass.MEASUREMENT not in sensor_state_classes
            ):
                return None
            if device_class not in DEVICE_CLASS_UNITS:
                return None
            if (
                device_class in DEVICE_CLASS_UNITS
                and unit not in DEVICE_CLASS_UNITS[device_class]
            ):
                return None

        return device_class