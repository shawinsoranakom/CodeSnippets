def _process_state_changed_event_into_session(
        self, event: Event[EventStateChangedData]
    ) -> None:
        """Process a state_changed event into the session."""
        state_attributes_manager = self.state_attributes_manager
        states_meta_manager = self.states_meta_manager
        entity_removed = not event.data.get("new_state")
        entity_id = event.data["entity_id"]

        dbstate = States.from_event(event)
        old_state = event.data["old_state"]

        assert self.event_session is not None
        session = self.event_session

        states_manager = self.states_manager
        if pending_state := states_manager.pop_pending(entity_id):
            dbstate.old_state = pending_state
            if old_state:
                pending_state.last_reported_ts = old_state.last_reported_timestamp
        elif old_state_id := states_manager.pop_committed(entity_id):
            dbstate.old_state_id = old_state_id
            if old_state:
                states_manager.update_pending_last_reported(
                    old_state_id, old_state.last_reported_timestamp
                )
        if entity_removed:
            dbstate.state = None
        else:
            states_manager.add_pending(entity_id, dbstate)

        if entity_id is None or not (
            shared_attrs_bytes := state_attributes_manager.serialize_from_event(event)
        ):
            return

        # Map the entity_id to the StatesMeta table
        if pending_states_meta := states_meta_manager.get_pending(entity_id):
            dbstate.states_meta_rel = pending_states_meta
        elif metadata_id := states_meta_manager.get(entity_id, session, True):
            dbstate.metadata_id = metadata_id
        elif entity_removed:
            # If the entity was removed, we don't need to add it to the
            # StatesMeta table or record it in the pending commit
            # if it does not have a metadata_id allocated to it as
            # it either never existed or was just renamed.
            return
        else:
            states_meta = StatesMeta(entity_id=entity_id)
            states_meta_manager.add_pending(states_meta)
            self._add_to_session(session, states_meta)
            dbstate.states_meta_rel = states_meta

        # Map the event data to the StateAttributes table
        shared_attrs = shared_attrs_bytes.decode("utf-8")
        # Matching attributes found in the pending commit
        if pending_event_data := state_attributes_manager.get_pending(shared_attrs):
            dbstate.state_attributes = pending_event_data
        # Matching attributes id found in the cache
        elif (
            attributes_id := state_attributes_manager.get_from_cache(shared_attrs)
        ) or (
            (hash_ := StateAttributes.hash_shared_attrs_bytes(shared_attrs_bytes))
            and (
                attributes_id := state_attributes_manager.get(
                    shared_attrs, hash_, session
                )
            )
        ):
            dbstate.attributes_id = attributes_id
        else:
            # No matching attributes found, save them in the DB
            dbstate_attributes = StateAttributes(shared_attrs=shared_attrs, hash=hash_)
            state_attributes_manager.add_pending(dbstate_attributes)
            self._add_to_session(session, dbstate_attributes)
            dbstate.state_attributes = dbstate_attributes

        self._add_to_session(session, dbstate)