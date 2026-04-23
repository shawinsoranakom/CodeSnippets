def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return sensor attributes if data is available."""
        if self._state is None or not self._attrs:
            return None

        delay = get_delay_in_minutes(self._attrs.departure.delay)
        departure = get_time_until(self._attrs.departure.time)

        attrs = {
            "destination": self._attrs.departure.station,
            "direction": self._attrs.departure.direction.name,
            "platform_arriving": self._attrs.arrival.platform,
            "platform_departing": self._attrs.departure.platform,
            "vehicle_id": self._attrs.departure.vehicle,
        }

        attrs["canceled"] = self._attrs.departure.canceled
        if attrs["canceled"]:
            attrs["departure"] = None
            attrs["departure_minutes"] = None
        else:
            attrs["departure"] = f"In {departure} minutes"
            attrs["departure_minutes"] = departure

        if self._show_on_map and self.station_coordinates:
            attrs[ATTR_LATITUDE] = self.station_coordinates[0]
            attrs[ATTR_LONGITUDE] = self.station_coordinates[1]

        if self.is_via_connection and not self._excl_vias:
            via = self._attrs.vias[0]

            attrs["via"] = via.station
            attrs["via_arrival_platform"] = via.arrival.platform
            attrs["via_transfer_platform"] = via.departure.platform
            attrs["via_transfer_time"] = get_delay_in_minutes(
                via.timebetween
            ) + get_delay_in_minutes(via.departure.delay)

        attrs["delay"] = f"{delay} minutes"
        attrs["delay_minutes"] = delay

        return attrs