def message_post(self, *,
                     body='', subject=None, message_type='notification',
                     email_from=None, author_id=None, parent_id=False,
                     subtype_xmlid=None, subtype_id=False,
                     partner_ids=None, outgoing_email_to=False,
                     incoming_email_to=False, incoming_email_cc=False,
                     attachments=None, attachment_ids=None, body_is_html=False,
                     **kwargs):
        """ Post a new message in an existing thread, returning the new mail.message.

        :param str|Markup body: body of the message, str content will be escaped, Markup
            for html body
        :param str subject: subject of the message
        :param str message_type: see mail_message.message_type field. Can be anything but
            user_notification, reserved for message_notify
        :param str email_from: from address of the author. See ``_message_compute_author``
            that uses it to make email_from / author_id coherent;
        :param int author_id: optional ID of partner record being the author. See
            ``_message_compute_author`` that uses it to make email_from / author_id coherent;
        :param int parent_id: handle thread formation
        :param str subtype_xmlid: optional xml id of a mail.message.subtype to
          fetch, will force value of subtype_id;
        :param int subtype_id: subtype_id of the message, used mainly for followers
            notification mechanism;
        :param list(int) partner_ids: partner_ids to notify in addition to partners
            computed based on subtype / followers matching;
        :param str outgoing_email_to: comma-separated list of emails to notify in
            addition to partner_ids. Experimental support as of Odoo v19;
        :param str incoming_email_to: comma-separated list of emails, already notified
            by incoming email;
        :param str incoming_email_cc: comma-separated list of emails, already notified
            by incoming email;
        :param list(tuple(str,str), tuple(str,str, dict)) attachments : list of attachment
            tuples in the form ``(name,content)`` or ``(name,content, info)`` where content
            is NOT base64 encoded;
        :param list attachment_ids: list of existing attachments to link to this message
            Should not be a list of commands. Attachment records attached to mail
            composer will be attached to the related document.
        :param bool body_is_html: indicates body should be threated as HTML even if str
            to be used only for RPC calls

        Extra keyword arguments will be used either
          * as default column values for the new mail.message record if they match
            mail.message fields;
          * propagated to notification methods if not;

        :return: newly create mail.message record
        """
        self.ensure_one()  # should always be posted on a record, use message_notify if no record

        # preliminary value safety check
        self._raise_for_invalid_parameters(
            set(kwargs.keys()),
            forbidden_names={'model', 'res_id', 'subtype'}
        )
        if self._name == 'mail.thread' or not self.id:
            raise ValueError(_("Posting a message should be done on a business document. Use message_notify to send a notification to an user."))
        if message_type == 'user_notification':
            raise ValueError(_("Use message_notify to send a notification to an user."))
        if attachments:
            # attachments should be a list (or tuples) of 3-elements list (or tuple)
            format_error = not is_list_of(attachments, list) and not is_list_of(attachments, tuple)
            if not format_error:
                format_error = not all(len(attachment) in {2, 3} for attachment in attachments)
            if format_error:
                raise ValueError(
                    _('Posting a message should receive attachments as a list of list or tuples (received %(aids)s)',
                      aids=repr(attachment_ids),
                     )
                )
        if attachment_ids and not is_list_of(attachment_ids, int):
            raise ValueError(
                _('Posting a message should receive attachments records as a list of IDs (received %(aids)s)',
                  aids=repr(attachment_ids),
                 )
            )
        attachment_ids = list(attachment_ids or [])
        if partner_ids and not is_list_of(partner_ids, int):
            raise ValueError(
                _('Posting a message should receive partners as a list of IDs (received %(pids)s)',
                  pids=repr(partner_ids),
                 )
            )
        partner_ids = list(partner_ids or [])

        # split message additional values from notify additional values
        msg_kwargs = {key: val for key, val in kwargs.items()
                      if key in self.env['mail.message']._fields}
        notif_kwargs = {key: val for key, val in kwargs.items()
                        if key not in msg_kwargs}

        # Add lang to context immediately since it will be useful in various flows later
        self = self._fallback_lang()

        # Find the message's author
        guest = self.env['mail.guest']._get_guest_from_context()
        if not author_id and self.env.user._is_public() and guest:
            author_guest_id = guest.id
            author_id, email_from = False, False
        else:
            author_guest_id = False
            author_id, email_from = self._message_compute_author(author_id, email_from)

        if subtype_xmlid:
            subtype_id = self.env['ir.model.data']._xmlid_to_res_id(subtype_xmlid)
        if not subtype_id:
            subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')

        # automatically subscribe recipients if asked to
        if self.env.context.get('mail_post_autofollow') and partner_ids:
            self.message_subscribe(partner_ids=list(partner_ids))
        # automatically subscribe customer recipient if model expects it
        elif partner_ids and self.env.context.get('mail_post_autofollow') is not False and self._mail_thread_customer:
            customer = self._mail_get_customer()
            if customer.id in partner_ids:
                self.message_subscribe(partner_ids=customer.ids)

        msg_values = dict(msg_kwargs)
        if 'email_add_signature' not in msg_values:
            msg_values['email_add_signature'] = True
        if body_is_html and self.env.user._is_internal():
            _logger.warning("Posting HTML message using body_is_html=True, use a Markup object instead (user: %s)",
                self.env.user.id)
            body = Markup(body)
        msg_values.update({
            # author
            'author_id': author_id,
            'author_guest_id': author_guest_id,
            'email_from': email_from,
            # document
            'model': self._name,
            'res_id': self.id,
            # content
            'body': escape(body),  # escape if text, keep if markup
            'message_type': message_type,
            'parent_id': self._message_compute_parent_id(parent_id),
            'subject': subject or False,
            'subtype_id': subtype_id,
            # recipients
            'partner_ids': partner_ids,
            'incoming_email_to': incoming_email_to,
            'incoming_email_cc': incoming_email_cc,
            'outgoing_email_to': outgoing_email_to,
        })
        # add default-like values afterwards, to avoid useless queries
        if 'record_alias_domain_id' not in msg_values:
            msg_values['record_alias_domain_id'] = self.sudo()._mail_get_alias_domains(default_company=self.env.company)[self.id].id
        if 'record_company_id' not in msg_values:
            msg_values['record_company_id'] = self._mail_get_companies(default=self.env.company)[self.id].id
        if 'reply_to' not in msg_values:
            msg_values['reply_to'] = self._notify_get_reply_to(default=email_from, author_id=author_id)[self.id]

        msg_values.update(
            self._process_attachments_for_post(attachments, attachment_ids, msg_values)
        )  # attachement_ids, body
        new_message = self._message_create([msg_values])

        # subscribe author(s) so that they receive answers; do it only when it is
        # a manual post by the author (aka not a system notification, not a message
        # posted 'in behalf of'). Limit to active and internal partners, as external
        # customers should be proposed through suggested recipients.
        author_subscribe = (
            not self.env.context.get('mail_post_autofollow_author_skip') and
            msg_values['message_type'] not in ('notification', 'user_notification', 'auto_comment', 'out_of_office') and
            subtype_id == self.env['ir.model.data']._xmlid_to_res_id('mail.mt_comment')
        )
        if author_subscribe:
            # TDE note: somehow propagate "real author" ?
            real_author = self._message_compute_real_author(msg_values['author_id'])
            if real_author and not real_author.partner_share:
                self._message_subscribe(partner_ids=[real_author.id])

        self._message_post_after_hook(new_message, msg_values)
        self._notify_thread(new_message, msg_values, **notif_kwargs)
        return new_message