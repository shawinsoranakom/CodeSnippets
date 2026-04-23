def _compute_event_registrations_sold_out(self):
        """Note that max seats limits for events and sum of limits for all its tickets may not be
        equal to enable flexibility.
        E.g. max 20 seats for ticket A, 20 seats for ticket B
            * With max 20 seats for the event
            * Without limit set on the event (=40, but the customer didn't explicitly write 40)
        When the event is multi slots, instead of checking if every tickets is sold out,
        checking if every slot-ticket combination is sold out.
        """
        for event in self:
            event.event_registrations_sold_out = (
                (event.seats_limited and event.seats_max and not event.seats_available > 0)
                or (event.event_ticket_ids and (
                    not any(availability is None or availability > 0
                        for availability in event._get_seats_availability([
                            (slot, ticket)
                            for slot in event.event_slot_ids
                            for ticket in event.event_ticket_ids
                        ])
                    )
                    if event.is_multi_slots else
                    all(ticket.is_sold_out for ticket in event.event_ticket_ids)
                ))
            )