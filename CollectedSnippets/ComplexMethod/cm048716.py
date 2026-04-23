def _get_default_sending_settings(self, move, from_cron=False, **custom_settings):
        """ Returns a dict with all the necessary data to generate and send invoices.
        Either takes the provided custom_settings, or the default value.
        """
        def get_setting(key, from_cron=False, default_value=None):
            return custom_settings.get(key) if key in custom_settings else move.sending_data.get(key) if from_cron else default_value

        vals = {
            'sending_methods': get_setting('sending_methods', default_value=self._get_default_sending_methods(move)) or {},
            'extra_edis': get_setting('extra_edis', default_value=self._get_default_extra_edis(move)) or {},
            'pdf_report': get_setting('pdf_report') or self._get_default_pdf_report_id(move),
            'author_user_id': get_setting('author_user_id', from_cron=from_cron) or self.env.user.id,
            'author_partner_id': get_setting('author_partner_id', from_cron=from_cron) or self.env.user.partner_id.id,
        }
        vals['invoice_edi_format'] = get_setting('invoice_edi_format', default_value=self._get_default_invoice_edi_format(move, sending_methods=vals['sending_methods']))
        mail_template = get_setting('mail_template') or self._get_default_mail_template_id(move)
        if 'email' in vals['sending_methods']:
            mail_lang = get_setting('mail_lang') or self._get_default_mail_lang(move, mail_template)
            vals.update({
                'mail_template': mail_template,
                'mail_lang': mail_lang,
                'mail_body': get_setting('mail_body', default_value=self._get_default_mail_body(move, mail_template, mail_lang)),
                'mail_subject': get_setting('mail_subject', default_value=self._get_default_mail_subject(move, mail_template, mail_lang)),
                'mail_partner_ids': get_setting('mail_partner_ids', default_value=self._get_default_mail_partner_ids(move, mail_template, mail_lang).ids),
                'reply_to': get_setting('reply_to') or self._get_mail_default_field_value_from_template(mail_template, mail_lang, move, 'reply_to'),
            })
        # Add mail attachments if sending methods support them
        if self._display_attachments_widget(vals['invoice_edi_format'], vals['sending_methods']):
            mail_attachments_widget = self._get_default_mail_attachments_widget(
                move,
                mail_template,
                invoice_edi_format=vals['invoice_edi_format'],
                extra_edis=vals['extra_edis'],
                pdf_report=vals['pdf_report'],
            )
            vals['mail_attachments_widget'] = get_setting('mail_attachments_widget', default_value=mail_attachments_widget)
        return vals