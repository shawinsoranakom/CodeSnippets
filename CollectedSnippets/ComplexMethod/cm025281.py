def extra_state_attributes(self) -> dict[str, Any]:
        """Return the optional state attributes."""
        props = {ATTR_ZONE_NUMBER: self._zone_number, ATTR_ZONE_SUMMARY: self._summary}
        if self._shade_type:
            props[ATTR_ZONE_SHADE] = self._shade_type
        if self._zone_type:
            props[ATTR_ZONE_TYPE] = self._zone_type
        if self._slope_type:
            if self._slope_type == SLOPE_FLAT:
                props[ATTR_ZONE_SLOPE] = "Flat"
            elif self._slope_type == SLOPE_SLIGHT:
                props[ATTR_ZONE_SLOPE] = "Slight"
            elif self._slope_type == SLOPE_MODERATE:
                props[ATTR_ZONE_SLOPE] = "Moderate"
            elif self._slope_type == SLOPE_STEEP:
                props[ATTR_ZONE_SLOPE] = "Steep"
        return props