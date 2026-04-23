def async_update_group_state(self) -> None:
        """Update state and attributes."""
        states = [
            state
            for entity_id in self._entity_ids
            if (state := self.hass.states.get(entity_id)) is not None
        ]

        # Set group as unavailable if all members are unavailable or missing
        self._attr_available = any(state.state != STATE_UNAVAILABLE for state in states)

        self._attr_is_closed = True
        self._attr_is_closing = False
        self._attr_is_opening = False
        self._attr_reports_position = False
        self._update_assumed_state_from_members()
        for state in states:
            if state.attributes.get(ATTR_CURRENT_POSITION) is not None:
                self._attr_reports_position = True
            if state.state == ValveState.OPEN:
                self._attr_is_closed = False
                continue
            if state.state == ValveState.CLOSED:
                continue
            if state.state == ValveState.CLOSING:
                self._attr_is_closing = True
                continue
            if state.state == ValveState.OPENING:
                self._attr_is_opening = True
                continue

        valid_state = any(
            state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE) for state in states
        )
        if not valid_state:
            # Set as unknown if all members are unknown or unavailable
            self._attr_is_closed = None

        self._attr_current_valve_position = reduce_attribute(
            states, ATTR_CURRENT_POSITION
        )

        supported_features = ValveEntityFeature(0)
        if self._valves[KEY_OPEN_CLOSE]:
            supported_features |= ValveEntityFeature.OPEN | ValveEntityFeature.CLOSE
        if self._valves[KEY_STOP]:
            supported_features |= ValveEntityFeature.STOP
        if self._valves[KEY_SET_POSITION]:
            supported_features |= ValveEntityFeature.SET_POSITION
        self._attr_supported_features = supported_features