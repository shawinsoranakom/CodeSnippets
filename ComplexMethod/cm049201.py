def _odoo_attendee_commands_m(self, microsoft_event):
        commands_attendee = []
        commands_partner = []

        microsoft_attendees = microsoft_event.attendees or []
        emails = [
            a.get('emailAddress').get('address')
            for a in microsoft_attendees
            if email_normalize(a.get('emailAddress').get('address'))
        ]
        existing_attendees = self.env['calendar.attendee']
        if microsoft_event.match_with_odoo_events(self.env):
            existing_attendees = self.env['calendar.attendee'].search([
                ('event_id', '=', microsoft_event.odoo_id(self.env)),
                ('email', 'in', emails)])
        elif self.env.user.partner_id.email not in emails:
            commands_attendee += [(0, 0, {'state': 'accepted', 'partner_id': self.env.user.partner_id.id})]
            commands_partner += [(4, self.env.user.partner_id.id)]
        partners = self.env['mail.thread']._partner_find_from_emails_single(emails, no_create=False)
        attendees_by_emails = {a.email: a for a in existing_attendees}
        partners_by_emails = {p.email_normalized: p for p in partners}
        for email, attendee_info in zip(emails, microsoft_attendees):
            partner = partners_by_emails.get(email_normalize(email) or email, self.env['res.partner'])
            # Responses from external invitations are stored in the 'responseStatus' field.
            # This field only carries the current user's event status because Microsoft hides other user's status.
            if self.env.user.email == email and microsoft_event.responseStatus:
                attendee_microsoft_status = microsoft_event.responseStatus.get('response', 'none')
            else:
                attendee_microsoft_status = attendee_info.get('status').get('response')
            state = ATTENDEE_CONVERTER_M2O.get(attendee_microsoft_status, 'needsAction')

            if email in attendees_by_emails:
                # Update existing attendees
                commands_attendee += [(1, attendees_by_emails[email].id, {'state': state})]
            elif partner:
                # Create new attendees
                commands_attendee += [(0, 0, {'state': state, 'partner_id': partner.id})]
                commands_partner += [(4, partner.id)]
                if attendee_info.get('emailAddress').get('name') and not partner.name:
                    partner.name = attendee_info.get('emailAddress').get('name')
        for odoo_attendee in attendees_by_emails.values():
            # Remove old attendees
            if odoo_attendee.email not in emails:
                commands_attendee += [(2, odoo_attendee.id)]
                commands_partner += [(3, odoo_attendee.partner_id.id)]
        return commands_attendee, commands_partner