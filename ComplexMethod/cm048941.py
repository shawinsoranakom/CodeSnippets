def _compute_unavailable_partner_ids(self):
        super()._compute_unavailable_partner_ids()
        complete_events = self.filtered(
            lambda event: event.start and event.stop and (event.stop > event.start or (event.stop >= event.start and event.allday)) and event.partner_ids)
        if not complete_events:
            return
        event_intervals = complete_events._get_events_interval()
        for event, event_interval in event_intervals.items():
            # Event_interval is empty when an allday event contains at least one day where the company is closed
            if not event_interval:
                continue
            start = event_interval._items[0][0]
            stop = event_interval._items[-1][1]
            schedule_by_partner = event.partner_ids._get_schedule(start, stop, merge=False)
            event.unavailable_partner_ids |= event._check_employees_availability_for_event(
                schedule_by_partner, event_interval)