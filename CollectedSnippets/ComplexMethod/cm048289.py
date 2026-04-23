def _process_tickets_form(self, event, form_details):
        """ Process posted data about ticket order. Generic ticket are supported
        for event without tickets (generic registration).

        :return: list of order per ticket: [{
            'id': if of ticket if any (0 if no ticket),
            'ticket': browse record of ticket if any (None if no ticket),
            'name': ticket name (or generic 'Registration' name if no ticket),
            'quantity': number of registrations for that ticket,
            'current_limit_per_order': maximum of ticket orderable
        }, {...}]
        """
        ticket_order = {}
        for key, value in form_details.items():
            registration_items = key.split('nb_register-')
            if len(registration_items) != 2:
                continue
            ticket_order[int(registration_items[1])] = int(value)

        ticket_dict = dict((ticket.id, ticket) for ticket in request.env['event.event.ticket'].sudo().search([
            ('id', 'in', [tid for tid in ticket_order.keys() if tid]),
            ('event_id', '=', event.id)
        ]))

        tickets = request.env['event.event.ticket'].browse(ticket_dict.keys())
        slot = request.env['event.slot'].browse(int(slot)) if (slot := form_details.get("event_slot_id", False)) else slot
        tickets_limits = tickets._get_current_limit_per_order(slot, event)

        return [{
            'id': tid if ticket_dict.get(tid) else 0,
            'ticket': ticket_dict.get(tid),
            'name': ticket_dict[tid]['name'] if ticket_dict.get(tid) else _('Registration'),
            'quantity': count,
            'current_limit_per_order': tickets_limits.get(tid, next(iter(tickets_limits.values()))),  # next is used if the ticket id isn't known (alone event case)
        } for tid, count in ticket_order.items() if count]