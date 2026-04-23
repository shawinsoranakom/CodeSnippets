def native_value(self):
        """Return the state of the sensor."""
        if self._key == "battery":
            return self._device.battery_level
        if self._key == "balance":
            return self._device.balance.get("value")
        if self._key == "ctemp":
            return self._device.temp_inner
        if self._key == "etemp":
            return self._device.temp_engine
        if self._key == "gsm_lvl":
            return self._device.gsm_level_percent
        if self._key == "fuel" and self._device.fuel:
            return self._device.fuel.get("val")
        if self._key == "errors" and self._device.errors:
            return self._device.errors.get("val")
        if self._key == "mileage" and self._device.mileage:
            return self._device.mileage.get("val")
        if self._key == "gps_count" and self._device.position:
            return self._device.position.get("sat_qty")
        return None