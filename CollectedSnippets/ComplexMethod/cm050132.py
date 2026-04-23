def assertMailTraces(self, recipients_info, mailing, records,
                         check_mail=True, is_cancel_not_sent=True, sent_unlink=False,
                         author=None, mail_links_info=None):
        """ Check content of traces. Traces are fetched based on a given mailing
        and records. Their content is compared to recipients_info structure that
        holds expected information. Links content may be checked, notably to
        assert shortening or unsubscribe links. Mail.mail records may optionally
        be checked.

        :param recipients_info: list[{
            # TRACE
            'email': (normalized) email used when sending email and stored on
              trace. May be empty, computed based on partner;
            'failure_type': optional failure type;
            'failure_reason': optional failure reason;
            'partner': res.partner record (may be empty),
            'record: linked record,
            'trace_status': outgoing / sent / open / reply / bounce / error / cancel (sent by default),
            # MAIL.MAIL
            'content': optional content that should be present in mail.mail body_html;
            'email_to_mail': optional email used for the mail, when different from the
              one stored on the trace itself (see 'email_to' in assertMailMail);
            'email_to_recipients': optional email used ofr the outgoing email,
              see 'assertSentEmail';
            'failure_type': propagated from trace;
            'failure_reason': propagated from trace;
            'mail_values': other mail.mail values for assertMailMail;
            }, { ... }]

        :param mailing: a mailing.mailing record from which traces have been
          generated;
        :param records: records given to mailing that generated traces. It is
          used notably to find traces using their IDs;
        :param check_mail: if True, also check mail.mail records that should be
          linked to traces unless not sent (trace_status == 'cancel');
        :param is_cancel_not_sent: if True, also check that no mail.mail/mail.message
          related to "cancel trace" have been created and disable check_mail for those.
        :param sent_unlink: it True, sent mail.mail are deleted and we check gateway
          output result instead of actual mail.mail records;
        :param mail_links_info: if given, should follow order of ``recipients_info``
          and give details about links. See ``assertLinkShortenedHtml`` helper for
          more details about content to give.
          Not tested for mail with trace status == 'cancel' if is_cancel_not_sent;
        :param author: author of sent mail.mail;
        """
        # map trace state to email state
        state_mapping = {
            'sent': 'sent',
            'open': 'sent',  # opened implies something has been sent
            'reply': 'sent',  # replied implies something has been sent
            'error': 'exception',
            'cancel': 'cancel',
            'bounce': 'cancel',
        }

        traces = self.env['mailing.trace'].search([
            ('mass_mailing_id', 'in', mailing.ids),
            ('res_id', 'in', records.ids)
        ])
        debug_info = '\n'.join(
            f'Trace: to {t.email} - state {t.trace_status} - res_id {t.res_id}'
            for t in traces
        )

        # ensure trace coherency
        self.assertTrue(all(s.model == records._name for s in traces))
        self.assertEqual(set(s.res_id for s in traces), set(records.ids))

        # check each traces
        if not mail_links_info:
            mail_links_info = [None] * len(recipients_info)
        for recipient_info, link_info, record in zip(recipients_info, mail_links_info, records):
            # check input
            invalid = set(recipient_info.keys()) - {
                'content',
                # email_to
                'email', 'email_to_mail', 'email_to_recipients',
                # mail.mail
                'mail_values',
                # email
                'email_values',
                # trace
                'partner', 'record', 'trace_status',
                'failure_type', 'failure_reason',
            }
            if invalid:
                raise AssertionError(f"assertMailTraces: invalid input {invalid}")

            # recipients
            partner = recipient_info.get('partner', self.env['res.partner'])
            email = recipient_info.get('email')
            if email is None and partner:
                email = partner.email_normalized
            email_to_mail = recipient_info.get('email_to_mail') or email
            email_to_recipients = recipient_info.get('email_to_recipients')
            # trace
            failure_type = recipient_info.get('failure_type')
            failure_reason = recipient_info.get('failure_reason')
            status = recipient_info.get('trace_status', 'sent')
            # content
            content = recipient_info.get('content')
            record = record or recipient_info.get('record')

            recipient_trace = traces.filtered(
                lambda t: (t.email == email or (not email and not t.email)) and \
                          t.trace_status == status and \
                          (t.res_id == record.id if record else True)
            )
            self.assertTrue(
                len(recipient_trace) == 1,
                'MailTrace: email %s (recipient %s, status: %s, record: %s): found %s records (1 expected)\n%s' % (
                    email, partner, status, record,
                    len(recipient_trace), debug_info)
            )
            mail_not_created = is_cancel_not_sent and recipient_trace.trace_status == 'cancel'
            self.assertTrue(mail_not_created or bool(recipient_trace.mail_mail_id_int))
            if 'failure_type' in recipient_info or status in ('error', 'cancel', 'bounce'):
                self.assertEqual(recipient_trace.failure_type, failure_type)
            if 'failure_reason' in recipient_info:
                self.assertEqual(recipient_trace.failure_reason, failure_reason)
            if mail_not_created:
                self.assertFalse(recipient_trace.mail_mail_id_int)
                self.assertFalse(self.env['mail.mail'].sudo().search(
                    [('model', '=', record._name), ('res_id', '=', record.id),
                     ('id', 'in', self._new_mails.ids)]))
                self.assertFalse(self.env['mail.message'].sudo().search(
                    [('model', '=', record._name), ('res_id', '=', record.id),
                     ('id', 'in', self._new_mails.mail_message_id.ids)]))

            if check_mail and not mail_not_created:
                if author is None:
                    author = self.env.user.partner_id

                # mail.mail specific values to check
                email_values = recipient_info.get('email_values', {})
                fields_values = {'mailing_id': mailing}
                if recipient_info.get('mail_values'):
                    fields_values.update(recipient_info['mail_values'])
                if 'failure_type' in recipient_info:
                    fields_values['failure_type'] = failure_type
                if 'failure_reason' in recipient_info:
                    fields_values['failure_reason'] = failure_reason
                if 'email_to_mail' in recipient_info:
                    fields_values['email_to'] = recipient_info['email_to_mail']
                if partner:
                    fields_values['recipient_ids'] = partner

                # specific for partner: email_formatted is used
                if partner:
                    if status == 'sent' and sent_unlink:
                        self.assertSentEmail(author, [partner])
                    else:
                        self.assertMailMail(
                            partner, state_mapping[status],
                            author=author,
                            content=content,
                            email_to_recipients=email_to_recipients,
                            fields_values=fields_values,
                            email_values=email_values,
                        )
                # specific if email is False -> could have troubles finding it if several falsy traces
                elif not email and status in ('cancel', 'bounce'):
                    self.assertMailMailWId(
                        recipient_trace.mail_mail_id_int, state_mapping[status],
                        author=author,
                        content=content,
                        email_to_recipients=email_to_recipients,
                        fields_values=fields_values,
                        email_values=email_values,
                    )
                else:
                    self.assertMailMailWEmails(
                        [email_to_mail], state_mapping[status],
                        author=author,
                        content=content,
                        email_to_recipients=email_to_recipients,
                        fields_values=fields_values,
                        email_values=email_values,
                    )

            if link_info and not mail_not_created:
                trace_mail = self._find_mail_mail_wrecord(record)
                for (anchor_id, url, is_shortened, add_link_params) in link_info:
                    link_params = {'utm_medium': 'Email', 'utm_source': mailing.name}
                    if add_link_params:
                        link_params.update(**add_link_params)
                    self.assertLinkShortenedHtml(
                        trace_mail.body_html,
                        (anchor_id, url, is_shortened),
                        link_params=link_params,
                    )