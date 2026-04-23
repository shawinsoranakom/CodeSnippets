def _message_add_default_recipients(self):
        """ Generic implementation for finding default recipient to mail on
        a recordset. This method is a generic implementation available for
        all models as we could send an email through mail templates on models
        not inheriting from mail.thread. For that purpose we use mail methods
        to find partners (customers) and primary emails.

        Override this method on a specific model to implement model-specific
        behavior. """
        res = {}
        customers = self._mail_get_partners()
        primary_emails = self._mail_get_primary_email()
        for record in self:
            email_cc_lst, email_to_lst = [], []
            # consider caller is going to filter / handle so don't filter anything
            recipients_all = customers.get(record.id)
            # to computation
            email_to = primary_emails[record.id]
            if not email_to:
                email_to = next(
                    (
                        record[fname] for fname in [
                            'email_from', 'x_email_from',
                            'email', 'x_email',
                            'partner_email',
                            'email_normalized',
                        ] if fname and fname in record and record[fname]
                    ), False
                )
            if email_to:
                # keep value to ease debug / trace update if cannot normalize
                email_to_lst = tools.mail.email_split_and_format_normalize(email_to) or [email_to]
            # cc computation
            cc_fn = next(
                (
                    fname for fname in ['email_cc', 'partner_email_cc', 'x_email_cc']
                    if fname in record and record[fname]
                ), False
            )
            if cc_fn:
                email_cc_lst = tools.mail.email_split_and_format_normalize(record[cc_fn]) or [record[cc_fn]]

            res[record.id] = {
                'email_cc_lst': email_cc_lst,
                'email_to_lst': email_to_lst,
                'partners': recipients_all,
            }
        return res