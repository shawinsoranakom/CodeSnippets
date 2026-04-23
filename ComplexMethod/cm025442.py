def _calculate_unit_of_measurement(self, new_state: State) -> str | None:
        """Return the calculated unit of measurement.

        The unit of measurement is that of the source sensor, adjusted based on the
        state characteristics.
        """

        base_unit: str | None = new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        unit: str | None = None
        stat_type = self._state_characteristic
        if self.is_binary and stat_type in STATS_BINARY_PERCENTAGE:
            unit = PERCENTAGE
        elif not base_unit:
            unit = None
        elif stat_type in STATS_NUMERIC_RETAIN_UNIT:
            unit = base_unit
        elif stat_type in STATS_NOT_A_NUMBER or stat_type in (
            STAT_COUNT,
            STAT_COUNT_BINARY_ON,
            STAT_COUNT_BINARY_OFF,
        ):
            unit = None
        elif stat_type == STAT_VARIANCE:
            unit = base_unit + "²"
        elif stat_type == STAT_CHANGE_SAMPLE:
            unit = base_unit + "/sample"
        elif stat_type == STAT_CHANGE_SECOND:
            unit = base_unit + "/s"

        return unit