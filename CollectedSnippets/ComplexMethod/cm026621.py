def _update_cost(self) -> None:
        """Update incurred costs."""
        if self._adapter.source_type == "grid":
            valid_units = VALID_ENERGY_UNITS
            default_price_unit: str | None = UnitOfEnergy.KILO_WATT_HOUR

        elif self._adapter.source_type == "gas":
            valid_units = VALID_ENERGY_UNITS_GAS
            # No conversion for gas.
            default_price_unit = None

        elif self._adapter.source_type == "water":
            valid_units = VALID_VOLUME_UNITS_WATER
            if self.hass.config.units is METRIC_SYSTEM:
                default_price_unit = UnitOfVolume.CUBIC_METERS
            else:
                default_price_unit = UnitOfVolume.GALLONS

        energy_state = self.hass.states.get(
            cast(str, self._config[self._adapter.stat_energy_key])
        )

        if energy_state is None:
            return

        state_class = energy_state.attributes.get(ATTR_STATE_CLASS)
        if state_class not in SUPPORTED_STATE_CLASSES:
            if not self._wrong_state_class_reported:
                self._wrong_state_class_reported = True
                _LOGGER.warning(
                    "Found unexpected state_class %s for %s",
                    state_class,
                    energy_state.entity_id,
                )
            return

        # last_reset must be set if the sensor is SensorStateClass.MEASUREMENT
        if (
            state_class == SensorStateClass.MEASUREMENT
            and ATTR_LAST_RESET not in energy_state.attributes
        ):
            return

        try:
            energy = float(energy_state.state)
        except ValueError:
            return

        try:
            energy_price, energy_price_unit = self._get_energy_price(
                valid_units, default_price_unit
            )
        except EntityNotFoundError:
            return
        except ValueError:
            energy_price = None

        if self._last_energy_sensor_state is None:
            # Initialize as it's the first time all required entities are in place or
            # only the price is missing. In the later case, cost will update the first
            # time the energy is updated after the price entity is in place.
            self._reset(energy_state)
            return

        if energy_price is None:
            return

        energy_unit: str | None = energy_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)

        if energy_unit is None or energy_unit not in valid_units:
            if not self._wrong_unit_reported:
                self._wrong_unit_reported = True
                _LOGGER.warning(
                    "Found unexpected unit %s for %s",
                    energy_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT),
                    energy_state.entity_id,
                )
            return

        if (
            state_class != SensorStateClass.TOTAL_INCREASING
            and energy_state.attributes.get(ATTR_LAST_RESET)
            != self._last_energy_sensor_state.attributes.get(ATTR_LAST_RESET)
        ) or (
            state_class == SensorStateClass.TOTAL_INCREASING
            and reset_detected(
                self.hass,
                cast(str, self._config[self._adapter.stat_energy_key]),
                energy,
                float(self._last_energy_sensor_state.state),
                self._last_energy_sensor_state,
            )
        ):
            # Energy meter was reset, reset cost sensor too
            energy_state_copy = copy.copy(energy_state)
            energy_state_copy.state = "0.0"
            self._reset(energy_state_copy)

        # Update with newly incurred cost
        old_energy_value = float(self._last_energy_sensor_state.state)
        cur_value = cast(float, self._attr_native_value)

        converted_energy_price = self._convert_energy_price(
            energy_price, energy_price_unit, energy_unit
        )

        self._attr_native_value = (
            cur_value + (energy - old_energy_value) * converted_energy_price
        )

        self._last_energy_sensor_state = energy_state