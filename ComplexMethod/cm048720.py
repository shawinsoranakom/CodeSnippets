def _get_mail_params(self, move, move_data):
        # We must ensure the newly created PDF are added. At this point, the PDF has been generated but not added
        # to 'mail_attachments_widget'.
        mail_attachments_widget = move_data.get('mail_attachments_widget')
        seen_attachment_ids = set()
        to_exclude = {x['name'] for x in mail_attachments_widget if x.get('skip')}
        for attachment_data in self._get_invoice_extra_attachments_data(move) + mail_attachments_widget:
            if attachment_data['name'] in to_exclude and not attachment_data.get('manual'):
                continue

            try:
                attachment_id = int(attachment_data['id'])
            except ValueError:
                continue

            seen_attachment_ids.add(attachment_id)

        mail_attachments = [
            (attachment.name, attachment.raw)
            for attachment in self.env['ir.attachment'].browse(list(seen_attachment_ids)).exists()
        ]

        params = {
            'author_id': move_data['author_partner_id'],
            'body': move_data['mail_body'],
            'subject': move_data['mail_subject'],
            'partner_ids': move_data['mail_partner_ids'],
            'attachments': mail_attachments,
        }
        if move_data.get('reply_to'):
            params['reply_to'] = move_data['reply_to']
        return params