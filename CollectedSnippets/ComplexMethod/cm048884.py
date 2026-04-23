def _sync_google2odoo(self, google_events: GoogleEvent, write_dates=None, default_reminders=()):
        """Synchronize Google recurrences in Odoo. Creates new recurrences, updates
        existing ones.

        :param google_events: Google recurrences to synchronize in Odoo
        :param write_dates: A dictionary mapping Odoo record IDs to their write dates.
        :param default_reminders:
        :return: synchronized odoo recurrences
        """
        write_dates = dict(write_dates or {})
        existing = google_events.exists(self.env)
        new = google_events - existing - google_events.cancelled()

        odoo_values = [
            dict(self._odoo_values(e, default_reminders), need_sync=False)
            for e in new
        ]
        new_odoo = self.with_context(dont_notify=True, skip_contact_description=True)._create_from_google(new, odoo_values)
        cancelled = existing.cancelled()
        cancelled_odoo = self.browse(cancelled.odoo_ids(self.env))

        # Check if it is a recurring event that has been rescheduled.
        # We have to check if an event already exists in Odoo.
        # Explanation:
        # A recurrent event with `google_id` is equal to ID_RANGE_TIMESTAMP can be rescheduled.
        # The new `google_id` will be equal to ID_TIMESTAMP.
        # We have to delete the event created under the old `google_id`.
        rescheduled_events = new.filter(lambda gevent: not gevent.is_recurrence_follower())
        if rescheduled_events:
            google_ids_to_remove = [event.full_recurring_event_id() for event in rescheduled_events]
            cancelled_odoo += self.env['calendar.event'].search([('google_id', 'in', google_ids_to_remove)])

        cancelled_odoo.exists()._cancel()
        synced_records = new_odoo + cancelled_odoo
        pending = existing - cancelled
        pending_odoo = self.browse(pending.odoo_ids(self.env)).exists()
        for gevent in pending:
            odoo_record = self.browse(gevent.odoo_id(self.env))
            if odoo_record not in pending_odoo:
                # The record must have been deleted in the mean time; nothing left to sync
                continue
            # Last updated wins.
            # This could be dangerous if google server time and odoo server time are different
            updated = parse(gevent.updated)
            # Use the record's write_date to apply Google updates only if they are newer than Odoo's write_date.
            odoo_record_write_date = write_dates.get(odoo_record.id, odoo_record.write_date)
            # Migration from 13.4 does not fill write_date. Therefore, we force the update from Google.
            if not odoo_record_write_date or updated >= pytz.utc.localize(odoo_record_write_date):
                vals = dict(self._odoo_values(gevent, default_reminders), need_sync=False)
                odoo_record.with_context(dont_notify=True)._write_from_google(gevent, vals)
                synced_records |= odoo_record

        return synced_records