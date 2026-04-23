def _mail_find_partner_from_emails(self, emails, records=None, force_create=False, extra_domain=False):
        """ Utility method to find partners from email addresses. See
        '_partner_find_from_emails' for more details. Main change is return
        type, which follows given input.

        :return: a list of partner records ordered as given emails.
          If no partner has been found and/or created for a given emails its
          matching partner is an empty record.
        :rtype: list[models.Model]
        """
        if records and isinstance(records, self.pool['mail.thread']):
            results = records._partner_find_from_emails(
                dict.fromkeys(records, emails), avoid_alias=True, no_create=not force_create,
            )
            all_partners = self.env['res.partner'].browse(
                {partner.id for partners in results.values() for partner in partners if partner.id}
            )
        else:
            all_partners = self.env['mail.thread']._partner_find_from_emails_single(
                emails, avoid_alias=True, no_create=not force_create,
            )
        results = []
        for email_input in emails:
            email_key = email_normalize(email_input) or email_input
            if not email_key:
                results.append(self.env['res.partner'])
            else:
                results.append(next(
                    (p for p in all_partners if p.email_normalized == email_key or p.email == email_key),
                    self.env['res.partner']
                ))
        return results