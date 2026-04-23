def _notify_by_web_push_prepare_payload(self, message, msg_vals=False, force_record_name=False):
        """ Returns dictionary containing message information for a browser device.
        This info will be delivered to a browser device via its recorded endpoint.
        REM: It is having a limit of 4000 bytes (4kb)

        :param str force_record_name: record_name to use instead of being
          related record's display_name;
        """
        msg_vals = msg_vals or {}
        author_id = msg_vals['author_id'] if 'author_id' in msg_vals else message.author_id.id
        model = msg_vals['model'] if 'model' in msg_vals else message.model
        title = force_record_name or message.record_name
        res_id = msg_vals['res_id'] if 'res_id' in msg_vals else message.res_id
        body = msg_vals['body'] if 'body' in msg_vals else message.body

        if author_id:
            author_name = self.env['res.partner'].browse(author_id).name
            title = "%s: %s" % (author_name, title)
            icon = "/web/image/res.partner/%d/avatar_128" % author_id
        else:
            icon = '/web/static/img/odoo-icon-192x192.png'

        if tools.is_html_empty(body) and message.attachment_ids:
            total_attachments = len(message.attachment_ids)
            # sudo: ir.attachment - access voice_ids linked to an attachment, if present.
            attachments = message.attachment_ids.sudo()

            def get_attachment_label(attachment):
                return self.env._("Voice Message") if attachment.voice_ids else attachment.name

            if total_attachments == 1:
                body = get_attachment_label(attachments[0])
            elif total_attachments == 2:
                body = self.env._(
                    "%(file1)s and %(file2)s",
                    file1=get_attachment_label(attachments[0]),
                    file2=get_attachment_label(attachments[1]),
                )
            else:
                body = self.env._(
                    "%(file1)s and %(count)d other attachments",
                    file1=get_attachment_label(attachments[0]),
                    count=total_attachments - 1,
                )

        return {
            'title': title,
            'options': {
                'body': html2plaintext(body, include_references=False) + self._generate_tracking_message(message),
                'icon': icon,
                'data': {
                    'model': model if model else '',
                    'res_id': res_id if res_id else '',
                }
            }
        }