def create(self, vals_list):
        # notification field: if not set, set if mail comes from an existing mail.message
        for values in vals_list:
            if 'is_notification' not in values and values.get('mail_message_id'):
                values['is_notification'] = True
            if values.get('scheduled_date'):
                parsed_datetime = self._parse_scheduled_datetime(values['scheduled_date'])
                values['scheduled_date'] = parsed_datetime.replace(tzinfo=None) if parsed_datetime else False
            else:
                values['scheduled_date'] = False  # void string crashes
        new_mails = super().create(vals_list)

        new_mails_w_attach = self.env['mail.mail']
        for mail, values in zip(new_mails, vals_list):
            if values.get('attachment_ids'):
                new_mails_w_attach += mail
        if new_mails_w_attach:
            new_mails_w_attach.attachment_ids.check_access('read')

        return new_mails