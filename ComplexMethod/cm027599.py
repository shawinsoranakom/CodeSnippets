def async_get_stored_states(self) -> list[StoredState]:
        """Get the set of states which should be stored.

        This includes the states of all registered entities, as well as the
        stored states from the previous run, which have not been created as
        entities on this run, and have not expired.
        """
        now = dt_util.utcnow()
        all_states = self.hass.states.async_all()
        # Entities currently backed by an entity object
        current_states_by_entity_id = {
            state.entity_id: state
            for state in all_states
            if not state.attributes.get(ATTR_RESTORED)
        }

        # Start with the currently registered states
        stored_states: list[StoredState] = []
        for entity_id, entity in self.entities.items():
            if entity_id not in current_states_by_entity_id:
                continue
            try:
                extra_data = entity.extra_restore_state_data
            except Exception:
                _LOGGER.exception(
                    "Error getting extra restore state data for %s", entity_id
                )
                continue
            stored_states.append(
                StoredState(
                    current_states_by_entity_id[entity_id],
                    extra_data,
                    now,
                )
            )
        expiration_time = now - STATE_EXPIRATION

        for entity_id, stored_state in self.last_states.items():
            # Don't save old states that have entities in the current run
            # They are either registered and already part of stored_states,
            # or no longer care about restoring.
            if entity_id in current_states_by_entity_id:
                continue

            # Don't save old states that have expired
            if stored_state.last_seen < expiration_time:
                continue

            stored_states.append(stored_state)

        return stored_states