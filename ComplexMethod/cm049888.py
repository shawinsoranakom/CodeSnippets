def _process_attachments_for_post(self, attachments, attachment_ids, message_values):
        """ Preprocess attachments for MailTread.message_post() or MailMail.create().
        Purpose is to

          * transfer attachments given by ``attachment_ids`` from the composer
            to the record (if any);
          * limit attachments manipulation when being a shared user: only those
            created by the user and linked to the composer are considered;
          * create attachments from ``attachments``. If those are linked to the
            content (body) through CIDs body is updated. CIDs are found and
            replaced by links to web/image as CIDs are not supported as it.

        Note that attachments are created/written in sudo as we consider at this
        point access is granted on related record and/or to post the linked
        message. The caller must verify the access rights accordingly. Indeed
        attachments rights are stricter than message rights which may lead to
        ACLs issues e.g. when posting on a readonly document or replying to
        a notification on a private document.

        :param list(tuple(str,str)) or list(tuple(str,str, dict)) attachments:
          list of attachment tuples in the form ``(name,content)`` or
          `(name,content, info)`` where content is NOT base64 encoded;
        :param list attachment_ids: list of existing attachments to link to this
          message;
        :param message_values: dictionary of values that will be used to create the
          message. It is used to find back record- or content- context;

        :return: new values for message: 'attachment_ids' and optionally
          'body' if CIDs have been transformed;
        :rtype: dict
        """
        # allow calling as a model method using model/res_id
        if 'res_id' in message_values:
            model, res_id = message_values['model'], message_values['res_id']
        else:
            self.ensure_one()
            model, res_id = self._name, self.id
        body = ''
        if message_values.get('body'):
            # at this point, body should be valid Markup; other content will be
            # escaped to avoid any issue
            body = escape(message_values['body']) if not is_html_empty(message_values['body']) else ''

        m2m_attachment_ids = []
        if attachment_ids:
            # taking advantage of cache looks better in this case, to check
            filtered_attachment_ids = self.env['ir.attachment'].sudo().browse(attachment_ids).filtered(
                lambda a: a.res_model in ('mail.compose.message', 'mail.scheduled.message') and a.create_uid.id == self.env.uid)
            # update filtered (pending) attachments to link them to the proper record
            if filtered_attachment_ids:
                filtered_attachment_ids.write({'res_model': model, 'res_id': res_id})
            # prevent public and portal users from using attachments that are not theirs
            if not self.env.user._is_internal():
                attachment_ids = filtered_attachment_ids.ids

            m2m_attachment_ids += [(4, att_id) for att_id in attachment_ids]

        # Handle attachments parameter, that is a dictionary of attachments
        return_values = {}
        if attachments: # generate
            body_cids, body_filenames = set(), set()
            if body:
                root = lxml.html.fromstring(body)
                # first list all attachments that will be needed in body
                for node in root.iter('img'):
                    if node.get('src', '').startswith('cid:'):
                        body_cids.add(node.get('src').split('cid:')[1])
                    elif node.get('data-filename'):
                        body_filenames.add(node.get('data-filename'))

            attachement_values_list = []
            attachement_extra_list = []
            # generate values
            for attachment in attachments:
                if len(attachment) == 2:
                    name, content = attachment
                    cid = False
                    info = {}
                elif len(attachment) == 3:
                    name, content, info = attachment
                    cid = info and info.get('cid')
                else:
                    continue

                if isinstance(content, str):
                    encoding = info and info.get('encoding')
                    try:
                        content = content.encode(encoding or "utf-8")
                    except UnicodeEncodeError:
                        content = content.encode("utf-8")
                elif isinstance(content, EmailMessage):
                    content = content.as_bytes()
                elif content is None:
                    continue
                attachement_values = {
                    'name': name,
                    'datas': base64.b64encode(content),
                    'type': 'binary',
                    'description': name,
                    'res_model': model,
                    'res_id': res_id,
                }
                token = False
                if (cid and cid in body_cids) or (name and name in body_filenames):
                    token = self.env['ir.attachment']._generate_access_token()
                    attachement_values['access_token'] = token
                attachement_values_list.append(attachement_values)

                # keep cid, name list and token synced with attachement_values_list length to match ids latter
                attachement_extra_list.append((cid, name, token, info))

            new_attachments = self._create_attachments_for_post(attachement_values_list, attachement_extra_list)
            attach_cid_mapping, attach_name_mapping = {}, {}
            for attachment, (cid, name, token, _info) in zip(new_attachments, attachement_extra_list):
                if cid:
                    attach_cid_mapping[cid] = (attachment.id, token)
                if name:
                    attach_name_mapping[name] = (attachment.id, token)
                m2m_attachment_ids.append((4, attachment.id))

            # note: right know we are only taking attachments and ignoring attachment_ids.
            if (body_cids or body_filenames) and body:
                postprocessed = False
                for node in root.iter('img'):
                    att_id, token = False, False
                    if node.get('src', '').startswith('cid:'):
                        cid = node.get('src').split('cid:')[1]
                        att_id, token = attach_cid_mapping.get(cid, (False, False))
                    if (not att_id or not token) and node.get('data-filename'):
                        att_id, token = attach_name_mapping.get(node.get('data-filename'), (False, False))
                    if att_id and token:
                        node.set('src', f'/web/image/{att_id}?access_token={token}')
                        postprocessed = True
                if postprocessed:
                    # tostring being a raw string, we have to respect I/O and return
                    # a valid Markup
                    return_values['body'] = Markup(lxml.html.tostring(root, pretty_print=False, encoding='unicode'))
        return_values['attachment_ids'] = m2m_attachment_ids
        return return_values