def _notify_by_email_get_base_mail_values(self, message, recipients_data, additional_values=None):
        """ Return model-specific and message-related values to be used when
        creating notification emails. It serves as a common basis for all
        notification emails based on a given message.

        :param record message: <mail.message> record being notified;
        :param list recipients_data: list of email recipients data based on <res.partner>
          records formatted using a list of dicts. See ``MailThread._notify_get_recipients()``;
        :param dict additional_values: optional additional values to add (ease
          custom calls and inheritance);

        :return: dictionary of values suitable for a <mail.mail> create;
        """
        mail_subject = message.subject
        if not mail_subject and self and hasattr(self, '_message_compute_subject'):
            mail_subject = self._message_compute_subject()
        if not mail_subject:
            mail_subject = message.record_name
        if mail_subject:
            # replace new lines by spaces to conform to email headers requirements
            mail_subject = ' '.join(mail_subject.splitlines())

        # compute references: set references to parents likely to be sent and add current message just to
        # have a fallback in case replies mess with Messsage-Id in the In-Reply-To (e.g. amazon
        # SES SMTP may replace Message-Id and In-Reply-To refers an internal ID not stored in Odoo)
        message_sudo = message.sudo()
        ancestors = self.env['mail.message'].sudo().search(
            [
                ('model', '=', message_sudo.model), ('res_id', '=', message_sudo.res_id),
                ('id', '!=', message_sudo.id),
                ('subtype_id', '!=', False),  # filters out logs
                ('message_id', '!=', False),  # ignore records that somehow don't have a message_id (non ORM created)
            ], limit=32, order='id DESC',  # take 32 last, hoping to find public discussions in it
        )

        # filter out internal messages, to fetch 'public discussion' first
        outgoing_types = ('comment', 'auto_comment', 'email', 'email_outgoing')
        history_ancestors = ancestors.sorted(lambda m: (
            not m.is_internal and not m.subtype_id.internal,
            m.message_type in outgoing_types,
            m.message_type not in ('user_notification', 'out_of_office'),  # user notif / out of office -> avoid if possible
        ), reverse=True)  # False before True unless reverse
        # order from oldest to newest
        ancestors = history_ancestors[:3].sorted('id')
        references = ' '.join(m.message_id for m in (ancestors + message_sudo))
        # prepare notification mail values
        base_mail_values = {
            'mail_message_id': message.id,
            'references': references,
        }
        if mail_subject != message.subject:
            base_mail_values['subject'] = mail_subject
        if additional_values:
            base_mail_values.update(additional_values)

        # prepare headers (as sudo as accessing mail.alias.domain, restricted)
        headers = base_mail_values.get('headers') or {}
        # prepare external emails to modify Msg[To] and enable Reply-All by
        # including external people (aka share partners to notify + emails
        # notified by incoming email (incoming_email_cc and incoming_email_to)
        # that were not transformed into partners to notify
        external_emails = [
            formataddr((r['name'], r['email_normalized']))
            for r in recipients_data if r['active'] and r['email_normalized'] and r['share']
        ]
        external_emails_normalized = [
            r['email_normalized']
            for r in recipients_data if r['active'] and r['email_normalized'] and r['share']
        ]
        external_emails += list({
            email for email in email_split_and_format_normalize(
                f"{message_sudo.incoming_email_to or ''},{message_sudo.incoming_email_cc or ''}"
            )
            if email_normalize(email) not in external_emails_normalized
        })
        if external_emails and len(external_emails) < self._CUSTOMER_HEADERS_LIMIT_COUNT:  # more than threshold = considered as public record (slide, forum, ...) -> do not leak
            headers['X-Msg-To-Add'] = ','.join(external_emails)
        # sudo: access to mail.alias.domain, restricted
        if message_sudo.record_alias_domain_id.bounce_email:
            headers['Return-Path'] = message_sudo.record_alias_domain_id.bounce_email
        headers = self._notify_by_email_get_headers(headers=headers)
        if headers:
            base_mail_values['headers'] = repr(headers)
        return base_mail_values