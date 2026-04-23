def _handle_coordinator_update(self) -> None:
        if not (live_measurement := self.coordinator.get_live_measurement()):
            return
        state = live_measurement.get(self.entity_description.key)
        if state is None:
            return
        if self.entity_description.key in (
            "accumulatedConsumption",
            "accumulatedProduction",
        ):
            # Value is reset to 0 at midnight, but not always strictly increasing
            # due to hourly corrections.
            # If device is offline, last_reset should be updated when it comes
            # back online if the value has decreased
            ts_local = dt_util.parse_datetime(live_measurement["timestamp"])
            if ts_local is not None:
                if self.last_reset is None or (
                    # native_value is float
                    state < 0.5 * self.native_value  # type: ignore[operator]
                    and (
                        ts_local.hour == 0
                        or (ts_local - self.last_reset) > timedelta(hours=24)
                    )
                ):
                    self._attr_last_reset = dt_util.as_utc(
                        ts_local.replace(hour=0, minute=0, second=0, microsecond=0)
                    )
        if self.entity_description.key == "powerFactor":
            state *= 100.0
        self._attr_native_value = state
        self.async_write_ha_state()