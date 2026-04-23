def async_update_callback(self):
        """Fire the event if reason is that state is updated."""
        if (
            self.sensor.state == self._last_state
            # Filter out non-button events if last event type is available
            or (
                self.sensor.last_event is not None
                and self.sensor.last_event["type"] != EVENT_BUTTON
            )
        ):
            return

        # Filter out old states. Can happen when events fire while refreshing
        now_updated = dt_util.parse_datetime(self.sensor.state["lastupdated"])
        last_updated = dt_util.parse_datetime(self._last_state["lastupdated"])

        if (
            now_updated is not None
            and last_updated is not None
            and now_updated <= last_updated
        ):
            return

        # Extract the press code as state
        if hasattr(self.sensor, "rotaryevent"):
            state = self.sensor.rotaryevent
        else:
            state = self.sensor.buttonevent

        self._last_state = dict(self.sensor.state)

        # Fire event
        data = {
            CONF_ID: self.event_id,
            CONF_DEVICE_ID: self.device_registry_id,
            CONF_UNIQUE_ID: self.unique_id,
            CONF_EVENT: state,
            CONF_LAST_UPDATED: self.sensor.lastupdated,
        }
        self.bridge.hass.bus.async_fire(ATTR_HUE_EVENT, data)