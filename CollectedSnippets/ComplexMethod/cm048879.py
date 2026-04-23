def _sync_google_calendar(self, calendar_service: GoogleCalendarService):
        self.ensure_one()
        results = self._sync_request(calendar_service)
        if not results:
            return False
        events, default_reminders, full_sync = results.values()
        events = self._sync_google_calendar_filter_remote_events(events)
        if not events and not self._check_pending_odoo_records():
            return False
        # Google -> Odoo
        send_updates = not full_sync
        events.clear_type_ambiguity(self.env)
        recurrences = events.filter(lambda e: e.is_recurrence())

        # We apply Google updates only if their write date is later than the write date in Odoo.
        # It's possible that multiple updates affect the same record, maybe not directly.
        # To handle this, we preserve the write dates in Odoo before applying any updates,
        # and use these dates instead of the current live dates.
        odoo_events = self.env['calendar.event'].browse((events - recurrences).odoo_ids(self.env))
        odoo_recurrences = self.env['calendar.recurrence'].browse(recurrences.odoo_ids(self.env))
        recurrences_write_dates = {r.id: r.write_date for r in odoo_recurrences}
        events_write_dates = {e.id: e.write_date for e in odoo_events}
        synced_recurrences = self.env['calendar.recurrence']._sync_google2odoo(recurrences, recurrences_write_dates)
        synced_events = self.env['calendar.event']._sync_google2odoo(events - recurrences, events_write_dates, default_reminders=default_reminders)

        # Odoo -> Google
        recurrences = self.env['calendar.recurrence']._get_records_to_sync(full_sync=full_sync)
        recurrences -= synced_recurrences
        recurrences.with_context(send_updates=send_updates)._sync_odoo2google(calendar_service)
        synced_events |= recurrences.calendar_event_ids - recurrences._get_outliers()
        synced_events |= synced_recurrences.calendar_event_ids - synced_recurrences._get_outliers()
        events = self.env['calendar.event']._get_records_to_sync(full_sync=full_sync)
        (events - synced_events).with_context(send_updates=send_updates)._sync_odoo2google(calendar_service)

        return bool(results) and (bool(events | synced_events) or bool(recurrences | synced_recurrences))