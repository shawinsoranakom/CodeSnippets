def _process_non_state_changed_event_into_session(self, event: Event) -> None:
        """Process any event into the session except state changed."""
        session = self.event_session
        assert session is not None
        dbevent = Events.from_event(event)

        # Map the event_type to the EventTypes table
        event_type_manager = self.event_type_manager
        if pending_event_types := event_type_manager.get_pending(event.event_type):
            dbevent.event_type_rel = pending_event_types
        elif event_type_id := event_type_manager.get(event.event_type, session, True):
            dbevent.event_type_id = event_type_id
        else:
            event_types = EventTypes(event_type=event.event_type)
            event_type_manager.add_pending(event_types)
            self._add_to_session(session, event_types)
            dbevent.event_type_rel = event_types

        if not event.data:
            self._add_to_session(session, dbevent)
            return

        event_data_manager = self.event_data_manager
        if not (shared_data_bytes := event_data_manager.serialize_from_event(event)):
            return

        # Map the event data to the EventData table
        shared_data = shared_data_bytes.decode("utf-8")
        # Matching attributes found in the pending commit
        if pending_event_data := event_data_manager.get_pending(shared_data):
            dbevent.event_data_rel = pending_event_data
        # Matching attributes id found in the cache
        elif (data_id := event_data_manager.get_from_cache(shared_data)) or (
            (hash_ := EventData.hash_shared_data_bytes(shared_data_bytes))
            and (data_id := event_data_manager.get(shared_data, hash_, session))
        ):
            dbevent.data_id = data_id
        else:
            # No matching attributes found, save them in the DB
            dbevent_data = EventData(shared_data=shared_data, hash=hash_)
            event_data_manager.add_pending(dbevent_data)
            self._add_to_session(session, dbevent_data)
            dbevent.event_data_rel = dbevent_data

        self._add_to_session(session, dbevent)