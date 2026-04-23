def _update_microsoft_recurrence(self, recurrence, events):
        """
        Update Odoo events from Outlook recurrence and events.
        """
        # get the list of events to update ...
        events_to_update = events.filter(lambda e: e.seriesMasterId == self.microsoft_id)
        if self.end_type in ['count', 'forever']:
            events_to_update = list(events_to_update)[:MAX_RECURRENT_EVENT]

        # ... and update them
        rec_values = {}
        update_events = self.env['calendar.event']
        for e in events_to_update:
            if e.type == "exception":
                event_values = self.env['calendar.event']._microsoft_to_odoo_values(e)
            elif e.type == "occurrence":
                event_values = self.env['calendar.event']._microsoft_to_odoo_recurrence_values(e)
            else:
                event_values = None

            if event_values:
                # keep event values to update the recurrence later
                if any(f for f in ('start', 'stop') if f in event_values):
                    rec_values[(self.id, event_values.get('start'), event_values.get('stop'))] = dict(
                        event_values, need_sync_m=False
                    )

                odoo_event = self.env['calendar.event'].browse(e.odoo_id(self.env)).exists().with_context(
                    no_mail_to_attendees=True, mail_create_nolog=True
                )
                odoo_event.with_context(dont_notify=True).write(dict(event_values, need_sync_m=False))
                update_events |= odoo_event

        # update the recurrence
        detached_events = self.with_context(dont_notify=True)._apply_recurrence(rec_values)
        detached_events._cancel_microsoft()

        return update_events