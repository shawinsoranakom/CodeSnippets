def _apply_recurrence(self, specific_values_creation=None, no_send_edit=False, generic_values_creation=None):
        """Create missing events in the recurrence and detach events which no longer
        follow the recurrence rules.
        :return: detached events
        """
        event_vals = []
        keep = self.env['calendar.event']
        if specific_values_creation is None:
            specific_values_creation = {}

        for recurrence in self.filtered('base_event_id'):
            recurrence.calendar_event_ids |= recurrence.base_event_id
            event = recurrence.base_event_id or recurrence._get_first_event(include_outliers=False)
            duration = event.stop - event.start
            if specific_values_creation:
                ranges = set([(x[1], x[2]) for x in specific_values_creation if x[0] == recurrence.id])
            else:
                ranges = recurrence._range_calculation(event, duration)

            events_to_keep, ranges = recurrence._reconcile_events(ranges)
            keep |= events_to_keep
            [base_values] = event.copy_data()
            values = []
            for start, stop in ranges:
                value = dict(base_values, start=start, stop=stop, recurrence_id=recurrence.id, follow_recurrence=True)
                if (recurrence.id, start, stop) in specific_values_creation:
                    value.update(specific_values_creation[(recurrence.id, start, stop)])
                if generic_values_creation and recurrence.id in generic_values_creation:
                    value.update(generic_values_creation[recurrence.id])
                values += [value]
            event_vals += values

        events = self.calendar_event_ids - keep
        detached_events = self._detach_events(events)
        context = {
            **clean_context(self.env.context),
            **{'no_mail_to_attendees': True, 'mail_create_nolog': True},
        }
        self.env['calendar.event'].with_context(context).create(event_vals)
        return detached_events