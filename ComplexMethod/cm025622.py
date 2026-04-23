def async_update_group_state(self) -> None:
        """Update state and attributes."""
        self._update_assumed_state_from_members()

        states = [
            state
            for entity_id in self._entity_ids
            if (state := self.hass.states.get(entity_id)) is not None
        ]

        # Set group as unavailable if all members are unavailable or missing
        self._attr_available = any(state.state != STATE_UNAVAILABLE for state in states)

        valid_state = any(
            state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE) for state in states
        )
        if not valid_state:
            # Set as unknown if all members are unknown or unavailable
            self._is_on = None
        else:
            # Set as ON if any member is ON
            self._is_on = any(state.state == STATE_ON for state in states)

        percentage_states = self._async_states_by_support_flag(
            FanEntityFeature.SET_SPEED
        )
        self._percentage = reduce_attribute(percentage_states, ATTR_PERCENTAGE)
        if (
            percentage_states
            and percentage_states[0].attributes.get(ATTR_PERCENTAGE_STEP)
            and attribute_equal(percentage_states, ATTR_PERCENTAGE_STEP)
        ):
            self._speed_count = (
                round(100 / percentage_states[0].attributes[ATTR_PERCENTAGE_STEP])
                or 100
            )
        else:
            self._speed_count = 100

        self._set_attr_most_frequent(
            "_oscillating", FanEntityFeature.OSCILLATE, ATTR_OSCILLATING
        )
        self._set_attr_most_frequent(
            "_direction", FanEntityFeature.DIRECTION, ATTR_DIRECTION
        )

        self._attr_supported_features = FanEntityFeature(
            reduce(
                ior, [feature for feature in SUPPORTED_FLAGS if self._fans[feature]], 0
            )
        )