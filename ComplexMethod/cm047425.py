def _get_test_email_from(self):
        self.ensure_one()
        email_from = False
        if from_filter_parts := self._parse_from_filter(self.from_filter):
            # find first found complete email in filter parts
            email_from = next((email for email in from_filter_parts if "@" in email), False)
            # no complete email -> consider noreply
            if not email_from:
                email_from = f"noreply@{from_filter_parts[0]}"
        if not email_from:
            # Fallback to current user email if there's no from filter
            email_from = self.env.user.email
        if not email_from or "@" not in email_from:
            raise UserError(_('Please configure an email on the current user to simulate '
                              'sending an email message via this outgoing server'))
        return email_from