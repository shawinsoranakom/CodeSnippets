def find_or_create(self, email, assert_valid_email=False):
        """ Find a partner with the given ``email`` or use :meth:`name_create`
        to create a new one.

        :param str email: email-like string, which should contain at least one email,
            e.g. ``"Raoul Grosbedon <r.g@grosbedon.fr>"``
        :param bool assert_valid_email: raise if no valid email is found
        :return: newly created record
        """
        if not email:
            raise ValueError(_('An email is required for find_or_create to work'))

        parsed_name, parsed_email_normalized = tools.parse_contact_from_email(email)
        if not parsed_email_normalized and assert_valid_email:
            raise ValueError(_('A valid email is required for find_or_create to work properly.'))

        if parsed_email_normalized:
            partners = self.search([('email', '=ilike', parsed_email_normalized)], limit=1)
            if partners:
                return partners

        create_values = {self._rec_name: parsed_name or parsed_email_normalized}
        if parsed_email_normalized:  # keep default_email in context
            create_values['email'] = parsed_email_normalized
        return self.create(create_values)