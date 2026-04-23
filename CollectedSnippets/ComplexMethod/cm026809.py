def async_update_doorbell_state(
        self, old_state: State | None, new_state: State
    ) -> None:
        """Handle link doorbell sensor state change to update HomeKit value."""
        assert self._char_doorbell_detected
        assert self._char_doorbell_detected_switch
        state = new_state.state
        if state == STATE_ON or (
            self.doorbell_is_event
            and old_state is not None
            and old_state.state != STATE_UNAVAILABLE
            and state not in (STATE_UNKNOWN, STATE_UNAVAILABLE)
        ):
            self._char_doorbell_detected.set_value(DOORBELL_SINGLE_PRESS)
            self._char_doorbell_detected_switch.set_value(DOORBELL_SINGLE_PRESS)
            _LOGGER.debug(
                "%s: Set linked doorbell %s sensor to %d",
                self.entity_id,
                self.linked_doorbell_sensor,
                DOORBELL_SINGLE_PRESS,
            )