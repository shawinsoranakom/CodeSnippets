def _get_default_mail_partner_ids(self, move, mail_template, mail_lang):
        # TDE FIXME: this should use standard composer / template code to be sure
        # it is aligned with standard recipients management. Todo later
        partners = self.env['res.partner'].with_company(move.company_id)
        if mail_template.use_default_to:
            defaults = move._message_get_default_recipients()[move.id]
            email_cc = defaults['email_to']
            email_to = defaults['email_to']
            partners |= partners.browse(defaults['partner_ids'])
        else:
            if mail_template.email_cc:
                email_cc = self._get_mail_default_field_value_from_template(mail_template, mail_lang, move, 'email_cc')
            else:
                email_cc = ''
            if mail_template.email_to:
                email_to = self._get_mail_default_field_value_from_template(mail_template, mail_lang, move, 'email_to')
            else:
                email_to = ''

        partners |= move._partner_find_from_emails_single(
            tools.email_split(email_cc or '') + tools.email_split(email_to or ''),
            no_create=False,
        )

        if not mail_template.use_default_to and mail_template.partner_to:
            partner_to = self._get_mail_default_field_value_from_template(mail_template, mail_lang, move, 'partner_to')
            partner_ids = mail_template._parse_partner_to(partner_to)
            partners |= self.env['res.partner'].sudo().browse(partner_ids).exists()
        return partners if self.env.context.get('allow_partners_without_mail') else partners.filtered('email')