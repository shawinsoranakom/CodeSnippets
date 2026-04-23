def _async_update_group_state(self, tr_state: State | None = None) -> None:
        """Update group state.

        Optionally you can provide the only state changed since last update
        allowing this method to take shortcuts.

        This method must be run in the event loop.
        """
        # To store current states of group entities. Might not be needed.
        if tr_state:
            self._see_state(tr_state)

        if not self._on_off:
            return

        if tr_state is None or (
            self._assumed_state and not tr_state.attributes.get(ATTR_ASSUMED_STATE)
        ):
            self._assumed_state = self.mode(self._assumed.values())

        elif tr_state.attributes.get(ATTR_ASSUMED_STATE):
            self._assumed_state = True

        num_on_states = len(self._on_states)
        # If all the entity domains we are tracking
        # have the same on state we use this state
        # and its hass.data[REG_KEY].on_off_mapping to off
        if num_on_states == 1:
            on_state = next(iter(self._on_states))
        # If we do not have an on state for any domains
        # we use None (which will be STATE_UNKNOWN)
        elif num_on_states == 0:
            self._state = None
            return
        if self.single_state_type_key:
            on_state = self.single_state_type_key.on_state
        # If the entity domains have more than one
        # on state, we use STATE_ON/STATE_OFF
        else:
            on_state = STATE_ON
        group_is_on = self.mode(self._on_off.values())
        if group_is_on:
            self._state = on_state
        elif self.single_state_type_key:
            self._state = self.single_state_type_key.off_state
        else:
            self._state = STATE_OFF