def _send_completed_mail(self):
        """ Send an email to the attendee when they have successfully completed a course. """
        template_to_records = dict()
        for record in self:
            template = record.channel_id.completed_template_id
            if template:
                template_to_records.setdefault(template, self.env['slide.channel.partner'])
                template_to_records[template] += record

        record_email_values = {}
        for template, records in template_to_records.items():
            record_values = template._generate_template(
                records.ids,
                ['attachment_ids',
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
                ]
            )
            for res_id, values in record_values.items():
                # attachments specific not supported currently, only attachment_ids
                values.pop('attachments', False)
                values['body'] = values.get('body_html')  # keep body copy in chatter
                record_email_values[res_id] = values

        mail_mail_values = []
        for record in self:
            email_values = record_email_values.get(record.id)

            if not email_values or not email_values.get('partner_ids'):
                continue

            email_values.update(
                author_id=record.channel_id.user_id.partner_id.id or self.env.company.partner_id.id,
                auto_delete=True,
                recipient_ids=[(4, pid) for pid in email_values['partner_ids']],
            )
            email_values['body_html'] = template._render_encapsulate(
                'mail.mail_notification_light', email_values['body_html'],
                add_context={
                    'model_description': _('Completed Course')  # tde fixme: translate into partner lang
                },
                context_record=record.channel_id,
            )
            mail_mail_values.append(email_values)

        if mail_mail_values:
            self.env['mail.mail'].sudo().create(mail_mail_values)