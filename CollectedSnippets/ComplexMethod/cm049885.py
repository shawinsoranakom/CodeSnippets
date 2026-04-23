def _partner_find_from_emails(self, records_emails, avoid_alias=True, ban_emails=None,
                                  filter_found=None, additional_values=None, no_create=False):
        """ Find or create partners based on emails. Result is contextualized
        based on records, calling 'Model._get_customer_information()' to populate
        new partners data. It relies on 'ResPartner._find_or_create_from_emails()'
        for name / email parsing and record creation.

        :param dict records_emails: for each record in self, list of emails linked
          to this record e.g. {<crm.lead, 4>: ['"Customer" <customer@test.example.com>']};
        :param bool avoid_alias: skip link for any email matching existing aliases
          notably to avoid creating contacts that could mess with mailgateway;
        :param list ban_emails: optional list of banished emails e.g. because
          it may interfere with master data like aliases;
        :param callable filter_found: if given, filters found partners based on emails;
        :param dict additional_values: optional email-key based dict, giving
          values to populate new partners. Added to default values coming from
          'Model._get_customer_information()';
        :param bool no_create: skip the 'create' part of 'find or create'. Allows
          to use tool as 'find and sort' without adding new partners in db;

        :return: for each record ID, a ResPartner recordset containing found
            (or created) partners based on given emails. As emails are normalized
            less partners maybe present compared to input if duplicates are
            present;
        :rtype: dict
        """
        if self and len(self) != len(records_emails):
            raise ValueError('Invoke with either self maching records_emails, either on a void recordset.')
        # when invoked through MailThread, ids may come from records_emails (not recommended tool usage)
        res_ids = self.ids or [record.id for record in records_emails]
        found_results = dict.fromkeys(res_ids, self.env['res.partner'])
        # email_key is email_normalized, unless email is wrong and cannot be normalized
        # in which case the raw input is used instead, to distinguish various wrong
        # inputs
        emails_all = []
        emails_key_all = []
        emails_key_company_id = {}
        emails_key_res_ids = defaultdict(list)

        # fetch company information (as sudo, as we should not crash for that)
        records_company = self.sudo()._mail_get_companies()
        # fetch model-related additional information
        emails_normalized_info = self._get_customer_information()
        for email_key, update in (additional_values or {}).items():
            emails_normalized_info.setdefault(email_key, {}).update(**update)

        # classify email / company and email / record IDs
        for record, mails in records_emails.items():
            mails = records_emails.get(record, [])
            record_company = records_company.get(record.id, self.env['res.company'])
            for mail in mails:
                mail_normalized = email_normalize(mail, strict=False)
                email_key = mail_normalized or mail
                emails_key_res_ids[email_key].append(record.id)
                if record_company and email_key:  # False is not interesting anyway
                    emails_key_company_id[email_key] = record_company.id
                emails_all.append(mail)
                emails_key_all.append(email_key)
        if not emails_all:  # early skip, no need to do searches / ...
            return found_results

        # fetch information used to find existing partners, beware portal/public who
        # cannot read followers
        followers = self.sudo().message_partner_ids if 'message_partner_ids' in self else self.env['res.partner']
        alias_emails = self.env['mail.alias.domain'].sudo()._find_aliases(emails_key_all) if avoid_alias else []
        ban_emails = (ban_emails or []) + alias_emails

        # inspired notably from odoo/odoo@80a0b45df806ffecfb068b5ef05ae1931d655810; final
        # ordering is search order defined in '_find_or_create_from_emails', which is id ASC
        def sort_key(p):
            return (
                p == self.env.user.partner_id,                      # prioritize user
                p in followers,                                     # then followers
                not p.partner_share,                                # prioritize internal users
                bool(p.user_ids),                                   # prioritize portal users
                p.company_id.id == emails_key_company_id.get(
                    p.email_normalized, False
                ),                                                  # then partner associated w/ record's company
                not p.company_id,                                   # then company-agnostic to avoid issues
            )

        partners = self.env['res.partner']._find_or_create_from_emails(
            emails_all,
            additional_values={
                mail_key: {
                    'company_id': emails_key_company_id.get(mail_key, False),
                    **emails_normalized_info.get(mail_key, {}),
                } for mail_key in emails_key_all
            },
            ban_emails=ban_emails,
            filter_found=filter_found,
            no_create=no_create,
            sort_key=sort_key,
            sort_reverse=True,  # False < True, simplified writing sort
        )

        for mail, partner in zip(emails_all, partners):
            mail_key = email_normalize(mail, strict=False) or mail
            for res_id in emails_key_res_ids[mail_key]:
                # use an "OR" to avoid duplicates in returned recordset
                found_results[res_id] |= partner
        return found_results