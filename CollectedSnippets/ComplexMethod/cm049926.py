def _get_test_email_from(self):
        self.ensure_one()
        if from_filter_parts := [part.strip() for part in (self.from_filter or '').split(",") if part.strip()]:
            # find first found complete email in filter parts
            if mail_from := next((email for email in from_filter_parts if "@" in email), None):
                return mail_from
            # the mail server is configured for a domain that matches the default email address
            alias_domains = self.env['mail.alias.domain'].sudo().search([])
            matching = next(
                (alias_domain for alias_domain in alias_domains
                 if self._match_from_filter(alias_domain.default_from_email, self.from_filter)
                ), False
            )
            if matching:
                return matching.default_from_email
            # fake default_from "odoo@domain"
            return f"odoo@{from_filter_parts[0]}"
        # no from_filter or from_filter is configured for a domain different that
        # the default_from of company's alias_domain -> fallback
        return super()._get_test_email_from()