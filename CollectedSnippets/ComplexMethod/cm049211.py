def _load_odoo_ids_from_db(self, env, force_model=None):
        """
        Map Microsoft events to existing Odoo events:
        1) extract unmapped events only,
        2) match Odoo events and Outlook events which have both a ICalUId set,
        3) match remaining events,
        Returns the list of mapped events
        """
        mapped_events = [e.id for e in self if e._odoo_id]

        # avoid mapping events if they are already all mapped
        if len(self) == len(mapped_events):
            return self

        unmapped_events = self.filter(lambda e: e.id not in mapped_events)

        # Query events OR recurrences, get organizer_id and universal_id values by splitting microsoft_id.
        model_env = force_model if force_model is not None else self._get_model(env)
        odoo_events = model_env.with_context(active_test=False).search([
            '|',
            ('ms_universal_event_id', "in", unmapped_events.uids),
            ('microsoft_id', "in", unmapped_events.ids)
        ]).with_env(env)

        # 1. try to match unmapped events with Odoo events using their iCalUId
        unmapped_events_with_uids = unmapped_events.filter(lambda e: e.iCalUId)
        odoo_events_with_uids = odoo_events.filtered(lambda e: e.ms_universal_event_id)
        mapping = {e.ms_universal_event_id: e.id for e in odoo_events_with_uids}

        for ms_event in unmapped_events_with_uids:
            odoo_id = mapping.get(ms_event.iCalUId)
            if odoo_id:
                ms_event._events[ms_event.id]['_odoo_id'] = odoo_id
                mapped_events.append(ms_event.id)

        # 2. try to match unmapped events with Odoo events using their id
        unmapped_events = self.filter(lambda e: e.id not in mapped_events)
        mapping = {e.microsoft_id: e for e in odoo_events}

        for ms_event in unmapped_events:
            odoo_event = mapping.get(ms_event.id)
            if odoo_event:
                ms_event._events[ms_event.id]['_odoo_id'] = odoo_event.id
                mapped_events.append(ms_event.id)

                # don't forget to also set the global event ID on the Odoo event to ease
                # and improve reliability of future mappings
                odoo_event.write({
                    'microsoft_id': ms_event.id,
                    'ms_universal_event_id': ms_event.iCalUId,
                    'need_sync_m': False,
                })

        return self.filter(lambda e: e.id in mapped_events)