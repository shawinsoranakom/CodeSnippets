def resolve_data(self, value: ZwaveValue) -> NumericSensorDataTemplateData:
        """Resolve helper class data for a discovered value."""

        if value.command_class == CommandClass.BATTERY and value.property_ in (
            "chargingStatus",
            "rechargeOrReplace",
        ):
            return NumericSensorDataTemplateData(
                ENTITY_DESC_KEY_BATTERY_LIST_STATE, None
            )
        if (
            value.command_class == CommandClass.BATTERY
            and value.property_ == "maximumCapacity"
        ):
            return NumericSensorDataTemplateData(
                ENTITY_DESC_KEY_BATTERY_MAXIMUM_CAPACITY, PERCENTAGE
            )
        if (
            value.command_class == CommandClass.BATTERY
            and value.property_ == "temperature"
        ):
            return NumericSensorDataTemplateData(
                ENTITY_DESC_KEY_BATTERY_TEMPERATURE, UnitOfTemperature.CELSIUS
            )

        if value.command_class == CommandClass.METER:
            try:
                meter_scale_type = get_meter_scale_type(value)
            except UnknownValueData:
                return NumericSensorDataTemplateData()

            unit = self.find_key_from_matching_set(meter_scale_type, METER_UNIT_MAP)
            # We do this because even though these are energy scales, they don't meet
            # the unit requirements for the energy device class.
            if meter_scale_type in (
                ElectricScale.PULSE_COUNT,
                ElectricScale.KILOVOLT_AMPERE_HOUR,
                ElectricScale.KILOVOLT_AMPERE_REACTIVE_HOUR,
            ):
                return NumericSensorDataTemplateData(
                    ENTITY_DESC_KEY_TOTAL_INCREASING, unit
                )
            # We do this because even though these are power scales, they don't meet
            # the unit requirements for the power device class.
            if meter_scale_type == ElectricScale.KILOVOLT_AMPERE_REACTIVE:
                return NumericSensorDataTemplateData(ENTITY_DESC_KEY_MEASUREMENT, unit)

            return NumericSensorDataTemplateData(
                self.find_key_from_matching_set(
                    meter_scale_type, METER_DEVICE_CLASS_MAP
                ),
                unit,
            )

        if value.command_class == CommandClass.SENSOR_MULTILEVEL:
            try:
                sensor_type = get_multilevel_sensor_type(value)
                multilevel_sensor_scale_type = get_multilevel_sensor_scale_type(value)
            except UnknownValueData:
                return NumericSensorDataTemplateData()
            unit = self.find_key_from_matching_set(
                multilevel_sensor_scale_type, MULTILEVEL_SENSOR_UNIT_MAP
            )
            if sensor_type == MultilevelSensorType.TARGET_TEMPERATURE:
                return NumericSensorDataTemplateData(
                    ENTITY_DESC_KEY_TARGET_TEMPERATURE, unit
                )
            key = self.find_key_from_matching_set(
                sensor_type, MULTILEVEL_SENSOR_DEVICE_CLASS_MAP
            )
            if key:
                return NumericSensorDataTemplateData(key, unit)

        if value.command_class == CommandClass.ENERGY_PRODUCTION:
            energy_production_parameter = get_energy_production_parameter(value)
            energy_production_scale_type = get_energy_production_scale_type(value)
            unit = self.find_key_from_matching_set(
                energy_production_scale_type, ENERGY_PRODUCTION_UNIT_MAP
            )
            key = self.find_key_from_matching_set(
                energy_production_parameter, ENERGY_PRODUCTION_DEVICE_CLASS_MAP
            )
            if key:
                return NumericSensorDataTemplateData(key, unit)

        return NumericSensorDataTemplateData()