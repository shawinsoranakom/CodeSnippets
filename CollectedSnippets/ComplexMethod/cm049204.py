def _write_from_microsoft(self, microsoft_event, vals):
        current_rrule = self.rrule
        # event_tz is written on event in Microsoft but on recurrence in Odoo
        vals['event_tz'] = microsoft_event.start.get('timeZone')
        super()._write_from_microsoft(microsoft_event, vals)
        new_event_values = self.env["calendar.event"]._microsoft_to_odoo_values(microsoft_event)
        # Edge case:  if the base event was deleted manually in 'self_only' update, skip applying recurrence.
        # Also skip when the base event is an exception (follow_recurrence=False), because its
        # modified time will differ from the seriesMaster pattern without the master having changed,
        # and entering the destructive path would clear all Microsoft IDs
        if (
            self._has_base_event_time_fields_changed(new_event_values) and
            (new_event_values['start'] >= self.base_event_id.start) and
            self.base_event_id.follow_recurrence
        ):
            # we need to recreate the recurrence, time_fields were modified.
            base_event_id = self.base_event_id
            # We archive the old events to recompute the recurrence. These events are already deleted on Microsoft side.
            # We can't call _cancel because events without user_id would not be deleted
            (self.calendar_event_ids - base_event_id).microsoft_id = False
            (self.calendar_event_ids - base_event_id).ms_universal_event_id = False
            (self.calendar_event_ids - base_event_id).unlink()
            base_event_id.with_context(dont_notify=True).write(dict(
                new_event_values, microsoft_id=False, ms_universal_event_id=False, need_sync_m=False
            ))
            if self.rrule == current_rrule:
                # if the rrule has changed, it will be recalculated below
                # There is no detached event now
                self.with_context(dont_notify=True)._apply_recurrence()
        else:
            time_fields = (
                    self.env["calendar.event"]._get_time_fields()
                    | self.env["calendar.event"]._get_recurrent_fields()
            )
            # We avoid to write time_fields because they are not shared between events.
            self.with_context(dont_notify=True)._write_events(dict({
                field: value
                for field, value in new_event_values.items()
                if field not in time_fields
                }, need_sync_m=False)
            )
        # We apply the rrule check after the time_field check because the microsoft ids are generated according
        # to base_event start datetime.
        if self.rrule != current_rrule:
            detached_events = self._apply_recurrence()
            detached_events.ms_universal_event_id = False
            detached_events.unlink()