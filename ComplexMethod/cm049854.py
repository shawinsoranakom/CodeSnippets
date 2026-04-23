def _message_get_default_recipients(self, with_cc=False, all_tos=False):
        """ Compute and filter default recipients to mail on a recordset.
        Heuristics is to find a customer (res.partner record) holding a
        email. Then we fallback on email fields, beginning with field optionally
        defined using `_primary_email` attribute. Email can be prioritized
        compared to partner if `_mail_defaults_to_email` class parameter is set.

        :param with_cc: take into account CC-like field. By default those are
          not considered as valid for 'default recipients' e.g. in mailings,
          automated actions, ...
        :param all_tos: DEPRECATED
        """
        def email_key(email):
            return email_normalize(email, strict=False) or email.strip()

        res = {}
        prioritize_email = getattr(self, '_mail_defaults_to_email', False)
        found = self._message_add_default_recipients()

        # ban emails: never propose odoobot nor aliases
        all_emails = []
        for defaults in found.values():
            all_emails += defaults['email_to_lst']
            if with_cc:
                all_emails += defaults['email_cc_lst']
            all_emails += defaults['partners'].mapped('email_normalized')
        ban_emails = [self.env.ref('base.partner_root').email_normalized]
        ban_emails += self.env['mail.alias.domain'].sudo()._find_aliases(
            [email_key(e) for e in all_emails if e and e.strip()]
        )

        # fetch default recipients for each record
        for record in self:
            defaults = found[record.id]
            customers = defaults['partners']
            email_cc_lst = defaults['email_cc_lst'] if with_cc else []
            email_to_lst = defaults['email_to_lst']

            # pure default recipients, skip public and banned emails
            recipients_all = customers.filtered(lambda p: not p.is_public and (not p.email_normalized or p.email_normalized not in ban_emails))
            recipients = customers.filtered(lambda p: not p.is_public and p.email_normalized and p.email_normalized not in ban_emails)
            # filter emails, skip banned mails
            email_cc_lst = [e for e in email_cc_lst if e not in ban_emails]
            email_to_lst = [e for e in email_to_lst if e not in ban_emails]

            # prioritize recipients: default unless asked through '_mail_defaults_to_email', or when no email_to
            if not prioritize_email or not email_to_lst:
                # if no valid recipients nor emails, fallback on recipients even
                # invalid to have at least some information
                if recipients:
                    partner_ids = recipients.ids
                    email_to = ''
                elif recipients_all and len(recipients_all) == len(email_to_lst) and all(
                    email in recipients_all.mapped('email') for email in email_to_lst
                ):
                    # here we just have partners with invalid emails, same as email fields
                    partner_ids = recipients_all.ids
                    email_to = ''
                else:
                    partner_ids = [] if email_to_lst else recipients_all.ids
                    email_to = ','.join(email_to_lst)
            # if emails match partners, use partners to have more information
            elif len(email_to_lst) == len(recipients) and all(
                tools.email_normalize(email) in recipients.mapped('email_normalized') for email in email_to_lst
            ):
                partner_ids = recipients.ids
                email_to = ''
            else:
                partner_ids = []
                email_to = ','.join(email_to_lst)
            res[record.id] = {
                'email_cc': ','.join(email_cc_lst),
                'email_to': email_to,
                'partner_ids': partner_ids,
            }
        return res