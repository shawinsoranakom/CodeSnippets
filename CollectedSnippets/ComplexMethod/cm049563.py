def _get_current_limit_per_order(self, event_slot=False, event=False):
        """ Compute the maximum possible number of tickets for an order, taking
        into account the given event_slot if applicable.
        If no ticket is created (alone event), event_id argument is used. Then
        return the dictionary with False as key. """
        event_slot.ensure_one() if event_slot else None
        if self:
            slots_seats_available = self.event_id._get_seats_availability([[event_slot, ticket] for ticket in self])
        else:
            return {False: event_slot.seats_available if event_slot else (event.seats_available if event.seats_limited else event.EVENT_MAX_TICKETS)}
        availabilities = {}
        for ticket, seats_available in zip(self, slots_seats_available):
            if not seats_available:  # "No limit"
                seats_available = ticket.limit_max_per_order or ticket.event_id.EVENT_MAX_TICKETS
            else:
                seats_available = min(ticket.limit_max_per_order or seats_available, seats_available)
            availabilities[ticket.id] = seats_available
        return availabilities