def registration_confirm(self, event, **post):
        """ Check before creating and finalize the creation of the registrations
            that we have enough seats for all selected tickets.
            If we don't, the user is instead redirected to page to register with a
            formatted error message. """
        try:
            request.env['ir.http']._verify_request_recaptcha_token('website_event_registration')
        except UserError:
            return request.redirect('/event/%s/register?registration_error_code=recaptcha_failed' % event.id)
        registrations_data = self._process_attendees_form(event, post)
        counter_per_combination = Counter((registration.get('event_slot_id', False), registration['event_ticket_id']) for registration in registrations_data)
        slot_ids = {slot_id for slot_id, _ in counter_per_combination if slot_id}
        ticket_ids = {ticket_id for _, ticket_id in counter_per_combination if ticket_id}
        slots_per_id = {slot.id: slot for slot in self.env['event.slot'].browse(slot_ids)}
        tickets_per_id = {ticket.id: ticket for ticket in self.env['event.event.ticket'].browse(ticket_ids)}
        try:
            event._verify_seats_availability(list({
                (slots_per_id.get(slot_id, False), tickets_per_id.get(ticket_id, False), count)
                for (slot_id, ticket_id), count in counter_per_combination.items()
            }))
        except ValidationError:
            return request.redirect('/event/%s/register?registration_error_code=insufficient_seats' % event.id)
        attendees_sudo = self._create_attendees_from_registration_post(event, registrations_data)

        return request.redirect(('/event/%s/registration/success?' % event.id) + werkzeug.urls.url_encode({'registration_ids': ",".join([str(id) for id in attendees_sudo.ids])}))