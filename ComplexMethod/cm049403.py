def _create_attendees_from_registration_post(self, event, registration_data):
        # we have at least one registration linked to a ticket -> sale mode activate
        if not any(info.get('event_ticket_id') for info in registration_data):
            return super()._create_attendees_from_registration_post(event, registration_data)

        event_ticket_ids = [registration['event_ticket_id'] for registration in registration_data if registration.get('event_ticket_id')]
        event_ticket_by_id = {
            event_ticket.id: event_ticket
            for event_ticket in request.env['event.event.ticket'].sudo().browse(event_ticket_ids)
        }

        if all(event_ticket.price == 0 for event_ticket in event_ticket_by_id.values()) and not request.cart.id:
            # all chosen tickets are free AND no existing SO -> skip SO and payment process
            return super()._create_attendees_from_registration_post(event, registration_data)

        order_sudo = request.cart or request.website._create_cart()
        tickets_data = defaultdict(int)
        for data in registration_data:
            event_slot_id = data.get('event_slot_id', False)
            event_ticket_id = data.get('event_ticket_id', False)
            if event_ticket_id:
                tickets_data[event_slot_id, event_ticket_id] += 1

        cart_data = {}
        for (slot_id, ticket_id), count in tickets_data.items():
            ticket_sudo = event_ticket_by_id.get(ticket_id)
            cart_values = order_sudo._cart_add(
                product_id=ticket_sudo.product_id.id,
                quantity=count,
                event_ticket_id=ticket_id,
                event_slot_id=slot_id,
            )
            cart_data[slot_id, ticket_id] = cart_values['line_id']

        for data in registration_data:
            event_slot_id = data.get('event_slot_id', False)
            event_ticket_id = data.get('event_ticket_id', False)
            event_ticket = event_ticket_by_id.get(event_ticket_id)
            if event_ticket:
                data['sale_order_id'] = order_sudo.id
                data['sale_order_line_id'] = cart_data[event_slot_id, event_ticket_id]

        return super()._create_attendees_from_registration_post(event, registration_data)