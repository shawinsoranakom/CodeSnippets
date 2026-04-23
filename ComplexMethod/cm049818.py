def send_mail_batch(self, res_ids, force_send=False, raise_exception=False, email_values=None,
                  email_layout_xmlid=False):
        """ Generates new mail.mails. Batch version of 'send_mail'.'

        :param list res_ids: IDs of modelrecords on which template will be rendered

        :returns: newly created mail.mail
        """
        # Grant access to send_mail only if access to related document
        self.ensure_one()
        self._send_check_access(res_ids)
        sending_email_layout_xmlid = email_layout_xmlid or self.email_layout_xmlid

        mails_sudo = self.env['mail.mail'].sudo()
        batch_size = int(
            self.env['ir.config_parameter'].sudo().get_param('mail.batch_size')
        ) or 50  # be sure to not have 0, as otherwise no iteration is done
        RecordModel = self.env[self.model].with_prefetch(res_ids)
        record_ir_model = self.env['ir.model']._get(self.model)

        for res_ids_chunk in tools.split_every(batch_size, res_ids):
            res_ids_values = self._generate_template(
                res_ids_chunk,
                ('attachment_ids',
                 'auto_delete',
                 'body_html',
                 'email_cc',
                 'email_from',
                 'email_to',
                 'mail_server_id',
                 'model',
                 'partner_to',
                 'reply_to',
                 'report_template_ids',
                 'res_id',
                 'scheduled_date',
                 'subject',
                )
            )
            values_list = [res_ids_values[res_id] for res_id in res_ids_chunk]

            # get record in batch to use the prefetch
            records = RecordModel.browse(res_ids_chunk)
            attachments_list = []

            # lang and company is used for rendering layout
            res_ids_langs, res_ids_companies = {}, {}
            if sending_email_layout_xmlid:
                if self.lang:
                    res_ids_langs = self._render_lang(res_ids_chunk)
                res_ids_companies = records._mail_get_companies(default=self.env.company)

            for record in records:
                values = res_ids_values[record.id]
                values['recipient_ids'] = [(4, pid) for pid in (values.get('partner_ids') or [])]
                values['attachment_ids'] = [(4, aid) for aid in (values.get('attachment_ids') or [])]
                values.update(email_values or {})

                # delegate attachments after creation due to ACL check
                attachments_list.append(values.pop('attachments', []))

                # add a protection against void email_from
                if 'email_from' in values and not values.get('email_from'):
                    values.pop('email_from')

                # encapsulate body
                if not sending_email_layout_xmlid:
                    values['body'] = values['body_html']
                    continue

                lang = res_ids_langs.get(record.id) or self.env.lang
                company = res_ids_companies.get(record.id) or self.env.company
                model_lang = record_ir_model.with_context(lang=lang)
                self_lang = self.with_context(lang=lang)
                record_lang = record.with_context(lang=lang)

                values['body_html'] = self_lang._render_encapsulate(
                    sending_email_layout_xmlid,
                    values['body_html'],
                    add_context={
                        'company': company,
                        'model_description': model_lang.display_name,
                    },
                    context_record=record_lang,
                )
                values['body'] = values['body_html']

            mails = self.env['mail.mail'].sudo().create(values_list)

            # manage attachments
            for mail, attachments in zip(mails, attachments_list):
                if attachments:
                    attachments_values = [
                        (0, 0, {
                            'name': name,
                            'datas': datas,
                            'type': 'binary',
                            'res_model': 'mail.message',
                            'res_id': mail.mail_message_id.id,
                        })
                        for (name, datas) in attachments
                    ]
                    mail.with_context(default_type=None).write({'attachment_ids': attachments_values})

            mails_sudo += mails

        if force_send:
            mails_sudo.send(raise_exception=raise_exception)
        return mails_sudo