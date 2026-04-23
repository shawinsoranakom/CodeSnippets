def find_or_create(self, email, assert_valid_email=False):
        """ Override to use the email_normalized field. """
        if not email:
            raise ValueError(_('An email is required for find_or_create to work'))

        parsed_name, parsed_email_normalized = tools.parse_contact_from_email(email)
        if not parsed_email_normalized and assert_valid_email:
            raise ValueError(_('%(email)s is not recognized as a valid email. This is required to create a new customer.'))
        if parsed_email_normalized:
            partners = self.search([('email_normalized', '=', parsed_email_normalized)], limit=1)
            if partners:
                return partners

        # We don't want to call `super()` to avoid searching twice on the email
        # Especially when the search `email =ilike` cannot be as efficient as
        # a search on email_normalized with a btree index
        # If you want to override `find_or_create()` your module should depend on `mail`
        create_values = {self._rec_name: parsed_name or parsed_email_normalized}
        if parsed_email_normalized:  # otherwise keep default_email in context
            create_values['email'] = parsed_email_normalized
        return self.create(create_values)