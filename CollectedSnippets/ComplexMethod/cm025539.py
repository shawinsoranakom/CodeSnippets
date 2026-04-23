def update(self) -> None:
        """Update the state."""
        super().update()
        if self.vera_device.category == veraApi.CATEGORY_TEMPERATURE_SENSOR:
            self._attr_native_value = self.vera_device.temperature

            vera_temp_units = self.vera_device.vera_controller.temperature_units

            if vera_temp_units == "F":
                self._attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
            else:
                self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

        elif self.vera_device.category in (
            veraApi.CATEGORY_LIGHT_SENSOR,
            veraApi.CATEGORY_UV_SENSOR,
        ):
            self._attr_native_value = self.vera_device.light
        elif self.vera_device.category == veraApi.CATEGORY_HUMIDITY_SENSOR:
            self._attr_native_value = self.vera_device.humidity
        elif self.vera_device.category == veraApi.CATEGORY_SCENE_CONTROLLER:
            controller = cast(veraApi.VeraSceneController, self.vera_device)
            value = controller.get_last_scene_id(True)
            time = controller.get_last_scene_time(True)
            if time == self.last_changed_time:
                self._attr_native_value = None
            else:
                self._attr_native_value = value
            self.last_changed_time = time
        elif self.vera_device.category == veraApi.CATEGORY_POWER_METER:
            self._attr_native_value = self.vera_device.power
        elif self.vera_device.is_trippable:
            tripped = self.vera_device.is_tripped
            self._attr_native_value = "Tripped" if tripped else "Not Tripped"
        else:
            self._attr_native_value = "Unknown"