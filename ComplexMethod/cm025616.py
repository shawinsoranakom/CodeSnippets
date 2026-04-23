def async_update_group_state(self) -> None:
        """Update state and attributes."""
        states = [
            state.state
            for entity_id in self._entity_ids
            if (state := self.hass.states.get(entity_id)) is not None
        ]

        valid_state = any(
            state not in (STATE_UNKNOWN, STATE_UNAVAILABLE) for state in states
        )

        # Set group as unavailable if all members are unavailable or missing
        self._attr_available = any(state != STATE_UNAVAILABLE for state in states)

        self._attr_is_closed = True
        self._attr_is_closing = False
        self._attr_is_opening = False
        self._update_assumed_state_from_members()
        for entity_id in self._entity_ids:
            if not (state := self.hass.states.get(entity_id)):
                continue
            if state.state == CoverState.OPEN:
                self._attr_is_closed = False
                continue
            if state.state == CoverState.CLOSED:
                continue
            if state.state == CoverState.CLOSING:
                self._attr_is_closing = True
                continue
            if state.state == CoverState.OPENING:
                self._attr_is_opening = True
                continue
        if not valid_state:
            # Set as unknown if all members are unknown or unavailable
            self._attr_is_closed = None

        position_covers = self._covers[KEY_POSITION]
        all_position_states = [self.hass.states.get(x) for x in position_covers]
        position_states: list[State] = list(filter(None, all_position_states))
        self._attr_current_cover_position = reduce_attribute(
            position_states, ATTR_CURRENT_POSITION
        )

        tilt_covers = self._tilts[KEY_POSITION]
        all_tilt_states = [self.hass.states.get(x) for x in tilt_covers]
        tilt_states: list[State] = list(filter(None, all_tilt_states))
        self._attr_current_cover_tilt_position = reduce_attribute(
            tilt_states, ATTR_CURRENT_TILT_POSITION
        )

        supported_features = CoverEntityFeature(0)
        if self._covers[KEY_OPEN_CLOSE]:
            supported_features |= CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE
        supported_features |= CoverEntityFeature.STOP if self._covers[KEY_STOP] else 0
        if self._covers[KEY_POSITION]:
            supported_features |= CoverEntityFeature.SET_POSITION
        if self._tilts[KEY_OPEN_CLOSE]:
            supported_features |= (
                CoverEntityFeature.OPEN_TILT | CoverEntityFeature.CLOSE_TILT
            )
        if self._tilts[KEY_STOP]:
            supported_features |= CoverEntityFeature.STOP_TILT
        if self._tilts[KEY_POSITION]:
            supported_features |= CoverEntityFeature.SET_TILT_POSITION
        self._attr_supported_features = supported_features