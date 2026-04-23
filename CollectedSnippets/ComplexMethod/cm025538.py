def __init__(
        self, vera_device: veraApi.VeraSensor, controller_data: ControllerData
    ) -> None:
        """Initialize the sensor."""
        self._temperature_units: str | None = None
        self.last_changed_time = None
        VeraEntity.__init__(self, vera_device, controller_data)
        self.entity_id = ENTITY_ID_FORMAT.format(self.vera_id)
        if self.vera_device.category == veraApi.CATEGORY_TEMPERATURE_SENSOR:
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
        elif self.vera_device.category == veraApi.CATEGORY_LIGHT_SENSOR:
            self._attr_device_class = SensorDeviceClass.ILLUMINANCE
        elif self.vera_device.category == veraApi.CATEGORY_HUMIDITY_SENSOR:
            self._attr_device_class = SensorDeviceClass.HUMIDITY
        elif self.vera_device.category == veraApi.CATEGORY_POWER_METER:
            self._attr_device_class = SensorDeviceClass.POWER
        if self.vera_device.category == veraApi.CATEGORY_LIGHT_SENSOR:
            self._attr_native_unit_of_measurement = LIGHT_LUX
        elif self.vera_device.category == veraApi.CATEGORY_UV_SENSOR:
            self._attr_native_unit_of_measurement = "level"
        elif self.vera_device.category == veraApi.CATEGORY_HUMIDITY_SENSOR:
            self._attr_native_unit_of_measurement = PERCENTAGE
        elif self.vera_device.category == veraApi.CATEGORY_POWER_METER:
            self._attr_native_unit_of_measurement = UnitOfPower.WATT