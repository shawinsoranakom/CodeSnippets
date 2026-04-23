def registration_new(self, event, **post):
        """ After (slot and) tickets selection, render attendee(s) registration form.
        Slot and tickets availability check already performed in the template. """
        tickets = self._process_tickets_form(event, post)
        slot_id = post.get('event_slot_id', False)
        # Availability check needed as the total number of tickets can exceed the event/slot available tickets
        availability_check = True
        # Double check to verify that we are ordering fewer tickets than the limit conditions set
        limit_check = not any(ticket['quantity'] > ticket['current_limit_per_order'] for ticket in tickets)
        if event.seats_limited:
            ordered_seats = 0
            for ticket in tickets:
                ordered_seats += ticket['quantity']
            seats_available = event.seats_available
            if slot_id:
                seats_available = request.env['event.slot'].browse(int(slot_id)).seats_available or 0
            if seats_available < ordered_seats:
                availability_check = False
        if not tickets:
            return False
        default_first_attendee = {}
        if not request.env.user._is_public():
            default_first_attendee = {
                "name": request.env.user.name,
                "email": request.env.user.email,
                "phone": request.env.user.phone,
            }
        else:
            visitor = request.env['website.visitor']._get_visitor_from_request()
            if visitor.email:
                default_first_attendee = {
                    "name": visitor.display_name,
                    "email": visitor.email,
                    "phone": visitor.mobile,
                }
        return request.env['ir.ui.view']._render_template("website_event.registration_attendee_details", {
            'tickets': tickets,
            'event_slot_id': slot_id,
            'event': event,
            'availability_check': availability_check,
            'default_first_attendee': default_first_attendee,
            'limit_check': limit_check,
        })