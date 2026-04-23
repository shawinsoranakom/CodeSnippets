def _check_slots_dates(self):
        multi_slots_event_ids = self.filtered(lambda event: event.is_multi_slots).ids
        if not multi_slots_event_ids:
            return
        min_max_slot_dates_per_event = {
            event: (min_start, max_end)
            for event, min_start, max_end in self.env['event.slot']._read_group(
                domain=[('event_id', 'in', multi_slots_event_ids)],
                groupby=['event_id'],
                aggregates=['start_datetime:min', 'end_datetime:max']
            )
        }
        events_w_slots_outside_bounds = []
        for event, (min_start, max_end) in min_max_slot_dates_per_event.items():
            if (not (event.date_begin <= min_start <= event.date_end) or
                not (event.date_begin <= max_end <= event.date_end)):
                events_w_slots_outside_bounds.append(event)
        if events_w_slots_outside_bounds:
            raise ValidationError(_(
                "These events cannot have slots scheduled outside of their time range:\n%(event_names)s",
                event_names="\n".join(f"- {event.name}" for event in events_w_slots_outside_bounds)
            ))