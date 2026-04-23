def _handle_websocket_update(self, event: WebsocketEvent) -> None:
        """Update the entity with new websocket data."""
        # Ignore this event if it belongs to a system other than this one:
        if event.system_id != self._system.system_id:
            return

        # Ignore this event if this entity hasn't expressed interest in its type:
        if event.event_type not in self._websocket_events_to_listen_for:
            return

        # Ignore this event if it belongs to a entity with a different serial
        # number from this one's:
        if (
            self._device
            and event.event_type in WEBSOCKET_EVENTS_REQUIRING_SERIAL
            and event.sensor_serial != self._device.serial
        ):
            return

        sensor_type: str | None
        if event.sensor_type:
            sensor_type = event.sensor_type.name
        else:
            sensor_type = None

        self._attr_extra_state_attributes.update(
            {
                ATTR_LAST_EVENT_INFO: event.info,
                ATTR_LAST_EVENT_SENSOR_NAME: event.sensor_name,
                ATTR_LAST_EVENT_SENSOR_TYPE: sensor_type,
                ATTR_LAST_EVENT_TIMESTAMP: event.timestamp,
            }
        )

        # It's unknown whether these events reach the base station (since the connection
        # is lost); we include this for completeness and coverage:
        if event.event_type in (EVENT_CONNECTION_LOST, EVENT_POWER_OUTAGE):
            self._online = False
            return

        # If the base station comes back online, set entities to available, but don't
        # instruct the entities to update their state (since there won't be anything new
        # until the next websocket event or REST API update:
        if event.event_type in (EVENT_CONNECTION_RESTORED, EVENT_POWER_RESTORED):
            self._online = True
            return

        self.async_update_from_websocket_event(event)
        self.async_write_ha_state()