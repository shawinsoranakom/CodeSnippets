async def async_update(self) -> None:
        """Get the latest data and update the states."""
        await self.api.async_update()

        self._attributes = {}

        data: EnturPublicTransportData = self.api.get_stop_info(self._stop)
        if data is None:
            self._state = None
            return

        if self._show_on_map and data.latitude and data.longitude:
            self._attributes[CONF_LATITUDE] = data.latitude
            self._attributes[CONF_LONGITUDE] = data.longitude

        if not (calls := data.estimated_calls):
            self._state = None
            return

        self._state = due_in_minutes(calls[0].expected_departure_time)
        self._icon = ICONS.get(calls[0].transport_mode, ICONS[DEFAULT_ICON_KEY])

        self._attributes[ATTR_ROUTE] = calls[0].front_display
        self._attributes[ATTR_ROUTE_ID] = calls[0].line_id
        self._attributes[ATTR_EXPECTED_AT] = calls[0].expected_departure_time.strftime(
            "%H:%M"
        )
        self._attributes[ATTR_REALTIME] = calls[0].is_realtime
        self._attributes[ATTR_DELAY] = calls[0].delay_in_min

        number_of_calls = len(calls)
        if number_of_calls < 2:
            return

        self._attributes[ATTR_NEXT_UP_ROUTE] = calls[1].front_display
        self._attributes[ATTR_NEXT_UP_ROUTE_ID] = calls[1].line_id
        self._attributes[ATTR_NEXT_UP_AT] = calls[1].expected_departure_time.strftime(
            "%H:%M"
        )
        self._attributes[ATTR_NEXT_UP_IN] = (
            f"{due_in_minutes(calls[1].expected_departure_time)} min"
        )
        self._attributes[ATTR_NEXT_UP_REALTIME] = calls[1].is_realtime
        self._attributes[ATTR_NEXT_UP_DELAY] = calls[1].delay_in_min

        if number_of_calls < 3:
            return

        for i, call in enumerate(calls[2:]):
            key_name = f"departure_#{i + 3}"
            self._attributes[key_name] = (
                f"{'' if bool(call.is_realtime) else 'ca. '}"
                f"{call.expected_departure_time.strftime('%H:%M')} {call.front_display}"
            )