def _prepare_user_input_lead_values(self):
        ''' This method prepares the user values dictionary for creating the lead '''
        self.ensure_one()
        input_lead_values = self._prepare_lead_values_from_user_input_lines()

        # Get the username (or the email if the user was imported from a spreadsheet)
        username = participant_name = self.partner_id.name or self.partner_id.email
        if not username:  # Public user
            participant_name = input_lead_values['user_nickname'] or input_lead_values['public_user_mail'] or _('New')
        lead_contact_name = username or input_lead_values['user_nickname']
        lead_title = _('%(participant_name)s %(category_name)s results',
                       participant_name=participant_name, category_name=_('live session') if self.is_session_answer else _('survey'))

        lead_values = {
            'contact_name': lead_contact_name,
            'description': input_lead_values['description'],
            'name': lead_title,
        }

        # Associate lead to the existing partner when known. Either because the person is connected
        # or because they received the survey with a unique token (by email for example).
        if self.partner_id.active:  # active is used for a protection against odoobot and public user's partner
            lead_values['partner_id'] = self.partner_id.id
        elif input_lead_values['public_user_mail']:  # Save email field answer otherwise
            lead_values['email_from'] = input_lead_values['public_user_mail']

        return lead_values