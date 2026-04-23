def message_notify(self, *,
                       body='', subject=False,
                       author_id=None, email_from=None,
                       model=False, res_id=False,
                       subtype_xmlid=None, subtype_id=False, partner_ids=False,
                       attachments=None, attachment_ids=None,
                       **kwargs):
        """ Shortcut allowing to notify partners of messages that should not be
        displayed on a document. It pushes notifications on inbox or by email
        depending on the user configuration, like other notifications.

        Default values
          * subtype_id: if not given, fallback on ``note`` to be consistent
            with what message_post does;

        :param str body: body of the message, usually raw HTML that will
          be sanitized
        :param str subject: subject of the message
        :param int author_id: optional ID of partner record being the author. See
          ``_message_compute_author`` that uses it to make email_from / author_id coherent;
        :param str email_from: from address of the author. See ``_message_compute_author``
          that uses it to make email_from / author_id coherent;
        :param str model: when invoked on MailThread directly, this method
          allows to push a notification on a given record (allows to notify
          on not thread-enabled records);
        :param int res_id: defines the record in combination with model;
        :param str subtype_xmlid: optional xml id of a mail.message.subtype to
          fetch, will force value of subtype_id;
        :param int subtype_id: subtype_id of the message, used mainly for followers
          notification mechanism;
        :param list(int) partner_ids: partner_ids to notify in addition to partners
            computed based on subtype / followers matching;
        :param list(tuple(str,str), tuple(str,str, dict)) attachments : list of attachment
            tuples in the form ``(name,content)`` or ``(name,content, info)`` where content
            is NOT base64 encoded;
        :param list attachment_ids: list of existing attachments to link to this message
            Should not be a list of commands. Attachment records attached to mail
            composer will be attached to the related document.

        Extra keyword arguments will be used either
          * as default column values for the new mail.message record if they match
            mail.message fields;
          * propagated to notification methods if not;

        :return: posted mail.message records
        """
        if self:
            self.ensure_one()
        if not partner_ids:
            _logger.warning('Message notify called without recipient_ids, skipping')
            return self.env['mail.message']

        # preliminary value safety check
        self._raise_for_invalid_parameters(
            set(kwargs.keys()),
            forbidden_names={
                'incoming_email_cc', 'incoming_email_to', 'message_id',
                'message_type', 'outgoing_email_to', 'parent_id',
            }
        )
        if attachments:
            # attachments should be a list (or tuples) of 3-elements list (or tuple)
            valid = all(isinstance(attachment, (list, tuple)) and len(attachment) in (3, 2) for attachment in attachments)
            if not valid:
                raise ValueError(
                    _('Notification should receive attachments as a list of list or tuples (received %(aids)s)',
                      aids=repr(attachment_ids),
                     )
                )
        if attachment_ids and not is_list_of(attachment_ids, int):
            raise ValueError(
                _('Notification should receive attachments records as a list of IDs (received %(aids)s)',
                  aids=repr(attachment_ids),
                 )
            )
        if not is_list_of(partner_ids, int):
            raise ValueError(
                _('Notification should receive partners given as a list of IDs (received %(pids)s)',
                  pids=repr(partner_ids),
                 )
            )

        # split message additional values from notify additional values
        msg_kwargs = {key: val for key, val in kwargs.items() if key in self.env['mail.message']._fields}
        notif_kwargs = {key: val for key, val in kwargs.items() if key not in msg_kwargs}
        # consider users mentionning themselves should receive notifications
        notif_kwargs['notify_author_mention'] = notif_kwargs.get('notify_author_mention', True)

        author_id, email_from = self._message_compute_author(author_id, email_from)

        # allow to link a notification to a document that does not inherit from
        # MailThread by supporting model / res_id, but then both value should be set
        if not model or not res_id:
            model, res_id = False, False

        if subtype_xmlid:
            subtype_id = self.env['ir.model.data']._xmlid_to_res_id(subtype_xmlid)
        if not subtype_id:
            subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')

        msg_values = {
            # author
            'author_id': author_id,
            'email_from': email_from,
            # document
            'model': self._name if self else model,
            'res_id': self.id if self else res_id,
            # content
            'body': escape(body),  # escape if text, keep if markup
            'is_internal': True,
            'message_type': 'user_notification',
            'subject': subject,
            'subtype_id': subtype_id,
            # recipients
            'message_id': generate_tracking_message_id('message-notify'),
            'partner_ids': partner_ids,
            # notification
            'email_add_signature': True,
        }
        msg_values.update(msg_kwargs)
        # add default-like values afterwards, to avoid useless queries
        if self:
            if 'record_alias_domain_id' not in msg_values:
                msg_values['record_alias_domain_id'] = self._mail_get_alias_domains(default_company=self.env.company)[self.id].id
            if 'record_company_id' not in msg_values:
                msg_values['record_company_id'] = self._mail_get_companies(default=self.env.company)[self.id].id
        if 'reply_to' not in msg_values:
            msg_values['reply_to'] = self._notify_get_reply_to(default=email_from, author_id=author_id)[self.id if self else False]

        msg_values.update(
            self._process_attachments_for_post(attachments, attachment_ids, msg_values)
        )  # attachement_ids, body

        new_message = self._message_create([msg_values])
        self._fallback_lang()._notify_thread(new_message, msg_values, **notif_kwargs)
        return new_message