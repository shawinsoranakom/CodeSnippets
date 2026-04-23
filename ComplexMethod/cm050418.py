def _get_partner_email_update(self, force_void=True):
        """Calculate if we should write the email on the related partner. When
        the email of the lead / partner is an empty string, we force it to False
        to not propagate a False on an empty string.

        Done in a separate method so it can be used in both ribbon and inverse
        and compute of email update methods.

        :param bool force_void: if False, skip when lead has a void email value.
          This is used notably to avoid propagating void lead value to a valid
          partner value.
        """
        self.ensure_one()
        if self.partner_id and (force_void or self.email_from) and self.email_from != self.partner_id.email:
            lead_email_normalized = tools.email_normalize(self.email_from) or self.email_from or False
            partner_email_normalized = tools.email_normalize(self.partner_id.email) or self.partner_id.email or False
            return lead_email_normalized != partner_email_normalized
        return False