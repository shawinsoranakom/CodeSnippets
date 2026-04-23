def _sync_microsoft2odoo(self, microsoft_events: MicrosoftEvent):
        """
        Synchronize Microsoft recurrences in Odoo.
        Creates new recurrences, updates existing ones.
        :return: synchronized odoo
        """
        existing = microsoft_events.match_with_odoo_events(self.env)
        cancelled = microsoft_events.cancelled()
        new = microsoft_events - existing - cancelled
        new_recurrence = new.filter(lambda e: e.is_recurrent())

        # create new events and reccurrences
        odoo_values = [
            dict(self._microsoft_to_odoo_values(e, with_ids=True), need_sync_m=False)
            for e in (new - new_recurrence)
        ]
        synced_events = self.with_context(dont_notify=True, skip_contact_description=True)._create_from_microsoft(new, odoo_values)
        synced_recurrences, updated_events = self._sync_recurrence_microsoft2odoo(existing, new_recurrence)
        synced_events |= updated_events

        # remove cancelled events and recurrences
        cancelled_recurrences = self.env['calendar.recurrence'].search([
            '|',
            ('ms_universal_event_id', 'in', cancelled.uids),
            ('microsoft_id', 'in', cancelled.ids),
        ])
        cancelled_events = self.browse([
            e.odoo_id(self.env)
            for e in cancelled
            if e.id not in [r.microsoft_id for r in cancelled_recurrences]
        ])
        cancelled_recurrences._cancel_microsoft()
        cancelled_events = cancelled_events.exists()
        cancelled_events._cancel_microsoft()

        synced_recurrences |= cancelled_recurrences
        synced_events |= cancelled_events | cancelled_recurrences.calendar_event_ids

        # Get sync lower bound days range for checking if old events must be updated in Odoo.
        ICP = self.env['ir.config_parameter'].sudo()
        lower_bound_day_range = ICP.get_param('microsoft_calendar.sync.lower_bound_range')

        # update other events
        for mevent in (existing - cancelled).filter(lambda e: e.lastModifiedDateTime):
            # Last updated wins.
            # This could be dangerous if microsoft server time and odoo server time are different
            if mevent.is_recurrence():
                odoo_event = self.env['calendar.recurrence'].browse(mevent.odoo_id(self.env)).exists()
            else:
                odoo_event = self.browse(mevent.odoo_id(self.env)).exists()

            if odoo_event:
                odoo_event_updated_time = pytz.utc.localize(odoo_event.write_date)
                ms_event_updated_time = parse(mevent.lastModifiedDateTime)

                # If the update comes from an old event/recurrence, check if time diff between updates is reasonable.
                old_event_update_condition = True
                if lower_bound_day_range:
                    update_time_diff = ms_event_updated_time - odoo_event_updated_time
                    old_event_update_condition = odoo_event._check_old_event_update_required(int(lower_bound_day_range), update_time_diff)

                if ms_event_updated_time >= odoo_event_updated_time and old_event_update_condition:
                    vals = dict(odoo_event._microsoft_to_odoo_values(mevent), need_sync_m=False)
                    odoo_event.with_context(dont_notify=True)._write_from_microsoft(mevent, vals)

                    if odoo_event._name == 'calendar.recurrence':
                        update_events = odoo_event._update_microsoft_recurrence(mevent, microsoft_events)
                        synced_recurrences |= odoo_event
                        synced_events |= update_events
                    else:
                        synced_events |= odoo_event

        return synced_events, synced_recurrences