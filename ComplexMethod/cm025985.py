def update_from_latest_data(self) -> None:
        """Update the entity from the latest data."""
        try:
            data = self.coordinator.data["current"]["pollution"]
        except KeyError:
            return

        if self.entity_description.key == SENSOR_KIND_LEVEL:
            aqi = data[f"aqi{self._locale}"]
            [(self._attr_native_value, self._attr_icon)] = [
                (name, icon)
                for (floor, ceiling), (name, icon) in POLLUTANT_LEVELS.items()
                if floor <= aqi <= ceiling
            ]
        elif self.entity_description.key == SENSOR_KIND_AQI:
            self._attr_native_value = data[f"aqi{self._locale}"]
        elif self.entity_description.key == SENSOR_KIND_POLLUTANT:
            symbol = data[f"main{self._locale}"]
            self._attr_native_value = symbol
            self._attr_extra_state_attributes.update(
                {
                    ATTR_POLLUTANT_SYMBOL: symbol,
                    ATTR_POLLUTANT_UNIT: POLLUTANT_UNITS[symbol],
                }
            )

        # Displaying the geography on the map relies upon putting the latitude/longitude
        # in the entity attributes with "latitude" and "longitude" as the keys.
        # Conversely, we can hide the location on the map by using other keys, like
        # "lati" and "long".
        #
        # We use any coordinates in the config entry and, in the case of a geography by
        # name, we fall back to the latitude longitude provided in the coordinator data:
        latitude = self.coordinator.config_entry.data.get(
            CONF_LATITUDE,
            self.coordinator.data["location"]["coordinates"][1],
        )
        longitude = self.coordinator.config_entry.data.get(
            CONF_LONGITUDE,
            self.coordinator.data["location"]["coordinates"][0],
        )

        if self.coordinator.config_entry.options[CONF_SHOW_ON_MAP]:
            self._attr_extra_state_attributes[ATTR_LATITUDE] = latitude
            self._attr_extra_state_attributes[ATTR_LONGITUDE] = longitude
            self._attr_extra_state_attributes.pop("lati", None)
            self._attr_extra_state_attributes.pop("long", None)
        else:
            self._attr_extra_state_attributes["lati"] = latitude
            self._attr_extra_state_attributes["long"] = longitude
            self._attr_extra_state_attributes.pop(ATTR_LATITUDE, None)
            self._attr_extra_state_attributes.pop(ATTR_LONGITUDE, None)