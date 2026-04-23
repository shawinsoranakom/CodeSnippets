def _odoo_attendee_commands(self, google_event):
        attendee_commands = []
        partner_commands = []
        google_attendees = google_event.attendees or []
        if len(google_attendees) == 0 and google_event.organizer and google_event.organizer.get('self', False):
            user = google_event.owner(self.env)
            google_attendees += [{
                'email': user.partner_id.email,
                'responseStatus': 'accepted',
            }]
        emails = [a.get('email') for a in google_attendees]
        existing_attendees = self.env['calendar.attendee']
        if google_event.exists(self.env):
            event = google_event.get_odoo_event(self.env)
            existing_attendees = event.attendee_ids
        attendees_by_emails = {tools.email_normalize(a.email): a for a in existing_attendees}
        partners = self._get_sync_partner(emails)
        for attendee in zip(emails, partners, google_attendees):
            email = attendee[0]
            if email in attendees_by_emails:
                # Update existing attendees
                attendee_commands += [(1, attendees_by_emails[email].id, {'state': attendee[2].get('responseStatus')})]
            else:
                # Create new attendees
                if attendee[2].get('self'):
                    partner = self.env.user.partner_id
                elif attendee[1]:
                    partner = attendee[1]
                else:
                    continue
                attendee_commands += [(0, 0, {'state': attendee[2].get('responseStatus'), 'partner_id': partner.id})]
                partner_commands += [(4, partner.id)]
                if attendee[2].get('displayName') and not partner.name:
                    partner.name = attendee[2].get('displayName')
        for odoo_attendee in attendees_by_emails.values():
            # Remove old attendees but only if it does not correspond to the current user.
            email = tools.email_normalize(odoo_attendee.email)
            if email not in emails and email != self.env.user.email:
                attendee_commands += [(2, odoo_attendee.id)]
                partner_commands += [(3, odoo_attendee.partner_id.id)]
        return attendee_commands, partner_commands