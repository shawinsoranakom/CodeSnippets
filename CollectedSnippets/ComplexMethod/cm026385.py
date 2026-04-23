def _load_data(self, data):  # noqa: C901
        """Load the sensor with relevant data."""
        # Check if we have a new measurement,
        # otherwise we do not have to update the sensor
        if self._measured == data.get(MEASURED):
            return False

        self._measured = data.get(MEASURED)
        sensor_type = self.entity_description.key

        if sensor_type.endswith(("_1d", "_2d", "_3d", "_4d", "_5d")):
            # update forecasting sensors:
            fcday = 0
            if sensor_type.endswith("_2d"):
                fcday = 1
            if sensor_type.endswith("_3d"):
                fcday = 2
            if sensor_type.endswith("_4d"):
                fcday = 3
            if sensor_type.endswith("_5d"):
                fcday = 4

            # update weather symbol & status text
            if sensor_type.startswith((SYMBOL, CONDITION)):
                try:
                    condition = data.get(FORECAST)[fcday].get(CONDITION)
                except IndexError:
                    _LOGGER.warning("No forecast for fcday=%s", fcday)
                    return False

                if condition:
                    new_state = condition.get(CONDITION)
                    if sensor_type.startswith(SYMBOL):
                        new_state = condition.get(EXACTNL)
                    if sensor_type.startswith("conditioncode"):
                        new_state = condition.get(CONDCODE)
                    if sensor_type.startswith("conditiondetailed"):
                        new_state = condition.get(DETAILED)
                    if sensor_type.startswith("conditionexact"):
                        new_state = condition.get(EXACT)

                    img = condition.get(IMAGE)

                    if new_state != self.state or img != self.entity_picture:
                        self._attr_native_value = new_state
                        self._attr_entity_picture = img
                        return True
                return False

            if sensor_type.startswith(WINDSPEED):
                # hass wants windspeeds in km/h not m/s, so convert:
                try:
                    self._attr_native_value = data.get(FORECAST)[fcday].get(
                        sensor_type[:-3]
                    )
                except IndexError:
                    _LOGGER.warning("No forecast for fcday=%s", fcday)
                    return False

                if self.state is not None:
                    self._attr_native_value = round(self.state * 3.6, 1)
                return True

            # update all other sensors
            try:
                self._attr_native_value = data.get(FORECAST)[fcday].get(
                    sensor_type[:-3]
                )
            except IndexError:
                _LOGGER.warning("No forecast for fcday=%s", fcday)
                return False
            return True

        if sensor_type == SYMBOL or sensor_type.startswith(CONDITION):
            # update weather symbol & status text
            if condition := data.get(CONDITION):
                if sensor_type == SYMBOL:
                    new_state = condition.get(EXACTNL)
                if sensor_type == CONDITION:
                    new_state = condition.get(CONDITION)
                if sensor_type == "conditioncode":
                    new_state = condition.get(CONDCODE)
                if sensor_type == "conditiondetailed":
                    new_state = condition.get(DETAILED)
                if sensor_type == "conditionexact":
                    new_state = condition.get(EXACT)

                img = condition.get(IMAGE)

                if new_state != self.state or img != self.entity_picture:
                    self._attr_native_value = new_state
                    self._attr_entity_picture = img
                    return True

            return False

        if sensor_type.startswith(PRECIPITATION_FORECAST):
            # update nested precipitation forecast sensors
            nested = data.get(PRECIPITATION_FORECAST)
            self._timeframe = nested.get(TIMEFRAME)
            self._attr_native_value = nested.get(
                sensor_type[len(PRECIPITATION_FORECAST) + 1 :]
            )
            return True

        if sensor_type in [WINDSPEED, WINDGUST]:
            # hass wants windspeeds in km/h not m/s, so convert:
            self._attr_native_value = data.get(sensor_type)
            if self.state is not None:
                self._attr_native_value = round(data.get(sensor_type) * 3.6, 1)
            return True

        if sensor_type == VISIBILITY:
            # hass wants visibility in km (not m), so convert:
            self._attr_native_value = data.get(sensor_type)
            if self.state is not None:
                self._attr_native_value = round(self.state / 1000, 1)
            return True

        # update all other sensors
        self._attr_native_value = data.get(sensor_type)
        if sensor_type.startswith(PRECIPITATION_FORECAST):
            result = {ATTR_ATTRIBUTION: data.get(ATTRIBUTION)}
            if self._timeframe is not None:
                result[TIMEFRAME_LABEL] = f"{self._timeframe} min"

            self._attr_extra_state_attributes = result

        result = {
            ATTR_ATTRIBUTION: data.get(ATTRIBUTION),
            STATIONNAME_LABEL: data.get(STATIONNAME),
        }
        if self._measured is not None:
            # convert datetime (Europe/Amsterdam) into local datetime
            local_dt = dt_util.as_local(self._measured)
            result[MEASURED_LABEL] = local_dt.strftime("%c")

        self._attr_extra_state_attributes = result
        return True