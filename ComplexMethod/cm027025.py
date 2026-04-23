async def async_update(self) -> None:
        """Get the latest data from Smappee and update the state."""
        await self._smappee_base.async_update()

        sensor_key = self.entity_description.key
        if sensor_key == "total_power":
            self._attr_native_value = self._service_location.total_power
        elif sensor_key == "total_reactive_power":
            self._attr_native_value = self._service_location.total_reactive_power
        elif sensor_key == "solar_power":
            self._attr_native_value = self._service_location.solar_power
        elif sensor_key == "alwayson":
            self._attr_native_value = self._service_location.alwayson
        elif sensor_key in (
            "phase_voltages_a",
            "phase_voltages_b",
            "phase_voltages_c",
        ):
            phase_voltages = self._service_location.phase_voltages
            if phase_voltages is not None:
                if sensor_key == "phase_voltages_a":
                    self._attr_native_value = phase_voltages[0]
                elif sensor_key == "phase_voltages_b":
                    self._attr_native_value = phase_voltages[1]
                elif sensor_key == "phase_voltages_c":
                    self._attr_native_value = phase_voltages[2]
        elif sensor_key in ("line_voltages_a", "line_voltages_b", "line_voltages_c"):
            line_voltages = self._service_location.line_voltages
            if line_voltages is not None:
                if sensor_key == "line_voltages_a":
                    self._attr_native_value = line_voltages[0]
                elif sensor_key == "line_voltages_b":
                    self._attr_native_value = line_voltages[1]
                elif sensor_key == "line_voltages_c":
                    self._attr_native_value = line_voltages[2]
        elif sensor_key in (
            "power_today",
            "power_current_hour",
            "power_last_5_minutes",
            "solar_today",
            "solar_current_hour",
            "alwayson_today",
        ):
            trend_value = self._service_location.aggregated_values.get(sensor_key)
            self._attr_native_value = (
                round(trend_value) if trend_value is not None else None
            )
        elif sensor_key == "load":
            self._attr_native_value = self._service_location.measurements.get(
                self.entity_description.sensor_id
            ).active_total
        elif sensor_key == "sensor":
            sensor_id, channel_id = self.entity_description.sensor_id.split("-")
            sensor = self._service_location.sensors.get(int(sensor_id))
            for channel in sensor.channels:
                if channel.get("channel") == int(channel_id):
                    self._attr_native_value = channel.get("value_today")
        elif sensor_key == "switch":
            cons = self._service_location.actuators.get(
                self.entity_description.sensor_id
            ).consumption_today
            if cons is not None:
                self._attr_native_value = round(cons / 1000.0, 2)