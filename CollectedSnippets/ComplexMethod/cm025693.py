def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        params = {}
        if self._times is not None:
            next_arrival_data = self._times[0]
            if ATTR_NEXT_ARRIVAL in next_arrival_data:
                next_arrival: datetime = next_arrival_data[ATTR_NEXT_ARRIVAL]
                params.update({ATTR_NEXT_ARRIVAL: next_arrival.isoformat()})
            if len(self._times) > 1:
                second_next_arrival_time: datetime = self._times[1][ATTR_NEXT_ARRIVAL]
                if second_next_arrival_time is not None:
                    second_arrival = second_next_arrival_time
                    params.update(
                        {ATTR_SECOND_NEXT_ARRIVAL: second_arrival.isoformat()}
                    )
            params.update(
                {
                    ATTR_ROUTE_ID: self._times[0][ATTR_ROUTE_ID],
                    ATTR_STOP_ID: self._stop_id,
                }
            )
        if self._name_data is not None:
            params.update(
                {
                    ATTR_ROUTE_NAME: self._name_data[ATTR_ROUTE_NAME],
                    ATTR_STOP_NAME: self._name_data[ATTR_STOP_NAME],
                }
            )
        return {k: v for k, v in params.items() if v}