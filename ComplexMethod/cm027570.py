def async_is_significant_change(
        self, new_state: State, *, extra_arg: Any | None = None
    ) -> bool:
        """Return if this was a significant change.

        Extra kwargs are passed to the extra significant checker.
        """
        old_data: tuple[State, Any] | None = self.last_approved_entities.get(
            new_state.entity_id
        )

        # First state change is always ok to report
        if old_data is None:
            self.last_approved_entities[new_state.entity_id] = (new_state, extra_arg)
            return True

        old_state, old_extra_arg = old_data

        # Handle state unknown or unavailable
        if new_state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            if new_state.state == old_state.state:
                return False

            self.last_approved_entities[new_state.entity_id] = (new_state, extra_arg)
            return True

        # If last state was unknown/unavailable, also significant.
        if old_state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            self.last_approved_entities[new_state.entity_id] = (new_state, extra_arg)
            return True

        functions = self.hass.data.get(DATA_FUNCTIONS)

        if functions is None:
            raise RuntimeError("Significant Change not initialized")

        check_significantly_changed = functions.get(new_state.domain)

        if check_significantly_changed is not None:
            result = check_significantly_changed(
                self.hass,
                old_state.state,
                old_state.attributes,
                new_state.state,
                new_state.attributes,
            )

            if result is False:
                return False

        if self.extra_significant_check is not None:
            result = self.extra_significant_check(
                self.hass,
                old_state.state,
                old_state.attributes,
                old_extra_arg,
                new_state.state,
                new_state.attributes,
                extra_arg,
            )

            if result is False:
                return False

        # Result is either True or None.
        # None means the function doesn't know. For now assume it's True
        self.last_approved_entities[new_state.entity_id] = (
            new_state,
            extra_arg,
        )
        return True