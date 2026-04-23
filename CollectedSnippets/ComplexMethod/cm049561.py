def _get_seats_availability(self, slot_tickets):
        """ Get availabilities for given combinations of slot / ticket. Returns
        a list following input order. None denotes no limit. """
        self.ensure_one()
        if not (all(len(item) == 2 for item in slot_tickets)):
            raise ValueError('Input should be a list of tuples containing slot, ticket')

        if any(slot for (slot, _ticket) in slot_tickets):
            slot_tickets_nb_registrations = {
                (slot.id, ticket.id): count
                for (slot, ticket, count) in self.env['event.registration'].sudo()._read_group(
                    domain=[('event_slot_id', '!=', False), ('event_id', 'in', self.ids),
                            ('state', 'in', ['open', 'done']), ('active', '=', True)],
                    groupby=['event_slot_id', 'event_ticket_id'],
                    aggregates=['__count']
                )
            }

        availabilities = []
        for slot, ticket in slot_tickets:
            available = None
            # event is constrained: max stands for either each slot, either global (no slots)
            if self.seats_limited and self.seats_max:
                if slot:
                    available = slot.seats_available
                else:
                    available = self.seats_available
            # ticket is constrained: max standard for either each slot / ticket, either global (no slots)
            if available != 0 and ticket and ticket.seats_max:
                if slot:
                    ticket_available = ticket.seats_max - slot_tickets_nb_registrations.get((slot.id, ticket.id), 0)
                else:
                    ticket_available = ticket.seats_available
                available = ticket_available if available is None else min(available, ticket_available)
            availabilities.append(available)
        return availabilities