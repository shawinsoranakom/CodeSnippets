def create(self, vals_list):
        tracking_values_list = []
        for values in vals_list:
            if not (self.env.su or self.env.user.has_group('base.group_user')):
                values.pop('author_id', None)
                values.pop('email_from', None)
                self = self.with_context({k: v for k, v in self.env.context.items() if k not in ['default_author_id', 'default_email_from']})  # noqa: PLW0642
            if 'email_from' not in values:  # needed to compute reply_to
                _author_id, email_from = self.env['mail.thread']._message_compute_author(values.get('author_id'), email_from=None)
                values['email_from'] = email_from
            if not values.get('message_id'):
                values['message_id'] = self._get_message_id(values)
            if 'reply_to' not in values:
                values['reply_to'] = self._get_reply_to(values)

            if not values.get('attachment_ids', True):
                # pop empty values
                del values['attachment_ids']
            # extract base64 images
            if 'body' in values:
                Attachments = self.env['ir.attachment'].with_context(clean_context(self.env.context))
                data_to_url = {}
                def base64_to_boundary(match):
                    key = match.group(2)
                    if not data_to_url.get(key):
                        name = match.group(4) if match.group(4) else 'image%s' % len(data_to_url)
                        try:
                            attachment = Attachments.create({
                                'name': name,
                                'datas': match.group(2),
                                'res_model': values.get('model'),
                                'res_id': values.get('res_id'),
                            })
                        except binascii_error:
                            _logger.warning("Impossible to create an attachment out of badly formated base64 embedded image. Image has been removed.")
                            return match.group(3)  # group(3) is the url ending single/double quote matched by the regexp
                        else:
                            attachment.generate_access_token()
                            attachments = values.setdefault('attachment_ids', [])
                            attachments.append((4, attachment.id))
                            data_to_url[key] = ['/web/image/%s?access_token=%s' % (attachment.id, attachment.access_token), name, attachment.id]
                    # data-attachment-id helps identify image attachments that are already inserted in the body
                    # this is notably used to avoid displaying them twice in the chatter
                    return f'{data_to_url[key][0]}{match.group(3)} alt="{data_to_url[key][1]}" data-attachment-id="{data_to_url[key][2]}"'
                values['body'] = _image_dataurl.sub(base64_to_boundary, values['body'] or '')

            # delegate creation of tracking after the create as sudo to avoid access rights issues
            tracking_values_list.append(values.pop('tracking_value_ids', False))

        messages = super().create(vals_list)

        # link back attachments to records, to filter out attachments linked to
        # the same records as the message (considered as ok if message is ok)
        # and check rights on other documents
        attachments_tocheck = self.env['ir.attachment']
        doc_to_attachment_ids = defaultdict(set)
        if all(isinstance(command, int) or command[0] in (4, 6)
               for values in vals_list
               for command in values.get('attachment_ids', ())):
            for values in vals_list:
                message_attachment_ids = set()
                for command in values.get('attachment_ids', ()):
                    if isinstance(command, int):
                        message_attachment_ids.add(command)
                    elif command[0] == 6:
                        message_attachment_ids |= set(command[2])
                    else:  # command[0] == 4:
                        message_attachment_ids.add(command[1])
                if message_attachment_ids:
                    key = (values.get('model'), values.get('res_id'))
                    doc_to_attachment_ids[key] |= message_attachment_ids

            attachment_ids_all = {
                attachment_id
                for doc_attachment_ids in doc_to_attachment_ids
                for attachment_id in doc_attachment_ids
            }
            AttachmentSudo = self.env['ir.attachment'].sudo().with_prefetch(list(attachment_ids_all))
            for (model, res_id), doc_attachment_ids in doc_to_attachment_ids.items():
                # check only attachments belonging to another model, access already
                # checked on message for other attachments
                attachments_tocheck += AttachmentSudo.browse(doc_attachment_ids).filtered(
                    lambda att: att.res_model != model or att.res_id != res_id
                ).sudo(False)
        else:
            attachments_tocheck = messages.attachment_ids  # fallback on read if any unknown command
        if attachments_tocheck:
            attachments_tocheck.check_access('read')

        for message, values, tracking_values_cmd in zip(messages, vals_list, tracking_values_list):
            if tracking_values_cmd:
                vals_lst = [dict(cmd[2], mail_message_id=message.id) for cmd in tracking_values_cmd if len(cmd) == 3 and cmd[0] == 0]
                other_cmd = [cmd for cmd in tracking_values_cmd if len(cmd) != 3 or cmd[0] != 0]
                if vals_lst:
                    self.env['mail.tracking.value'].sudo().create(vals_lst)
                if other_cmd:
                    message.sudo().write({'tracking_value_ids': tracking_values_cmd})

            if message._is_thread_message_visible(vals=values):
                message._invalidate_documents(values.get('model'), values.get('res_id'))

        return messages