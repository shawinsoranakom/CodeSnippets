def assertMailNotifications(self, messages, recipients_info, bus_notif_count=1):
        """ Check bus notifications content. Mandatory and basic check is about
        channels being notified. Content check is optional.

        GENERATED INPUT
        :param <mail.message> messages: generated messages to check, coming
          notably from the 'self._new_msgs' filled during the mock;

        EXPECTED
        :param list recipients_info: list of data dict: [
          {
            # message values
            'content': message content that should be present in message 'body'
              field;
            'message_type': 'message_type' value (default: 'comment'),
            'subtype': xml id of message subtype (default: 'mail.mt_comment'),
            # notifications values
            'email_values': values to check in outgoing emails, check 'assertMailMail'
              and 'assertSentEmail';
            'mail_mail_values': values to check in generated <mail.mail>, check
              'assertMailMail';
            'message_values': values to check in found <mail.message>, check
              'assertMessageFields';
            'notif': list of notified recipients: [
              {
                'check_send': whether outgoing stuff has to be checked;
                'email_to': email if sent without partner,
                'email_to_recipients': propagated to 'assertMailMail';
                'failure_type': 'failure_type' on mail.notification;
                'is_read': 'is_read' on mail.notification;
                'partner': res.partner record (may be empty),
                'status': 'notification_status' on mail.notification;
                'type': 'notification_type' on mail.notification;
              },
              { ... }
            ],
          },
          {...}
        ]

        PARAMETERS
        :param mail_unlink_sent: mock parameter, tells if mails are unlinked
          and therefore we are able to check outgoing emails;
        """
        partners = self.env['res.partner'].sudo().concat(*list(p['partner'] for i in recipients_info for p in i['notif'] if p.get('partner')))
        email_addrs = [email for i in recipients_info for p in i['notif'] for email in p.get('email_to', []) if not p.get('partner')]
        base_domain = ['|', ('res_partner_id', 'in', partners.ids), ('mail_email_address', 'in', email_addrs)]
        if messages is not None:
            base_domain += [('mail_message_id', 'in', messages.ids)]
        notifications = self.env['mail.notification'].sudo().search(base_domain)
        debug_info = '\n-'.join(
            f'Notif: partner {notif.res_partner_id.id} ({notif.res_partner_id.name}) / type {notif.notification_type}'
            for notif in notifications
        )

        done_msgs = self.env['mail.message'].sudo()
        done_notifs = self.env['mail.notification'].sudo()

        for message_info in recipients_info:
            # sanity check
            extra_keys = set(message_info.keys()) - {
                'content',
                'email_to_recipients',
                'email_values',
                'mail_mail_values',
                'message_type',
                'message_values',
                'notif',
                'subtype',
            }
            if extra_keys:
                raise ValueError(f'Unsupported values: {extra_keys}')

            mbody, mtype = message_info.get('content', ''), message_info.get('message_type', 'comment')
            message_values = message_info.get('message_values', {})
            msubtype = message_info.get('message_values', {}).get('subtype_id', self.env.ref(message_info.get('subtype', 'mail.mt_comment')))

            # find message
            if messages:
                message = messages.filtered(lambda message: (
                    mbody in message.body and message.message_type == mtype and
                    msubtype == message.subtype_id
                ))
                debug_info = '\n'.join(
                    f'Msg: message_type {message.message_type}, subtype {message.subtype_id.name}, content {message.body}'
                    for message in messages
                )
            else:
                message = self.env['mail.message'].sudo().search([
                    ('body', 'ilike', mbody),
                    ('message_type', '=', mtype),
                    ('subtype_id', '=', msubtype.id)
                ], limit=1, order='id DESC')
                debug_info = ''
            self.assertTrue(message, 'Mail: not found message (content: %s, message_type: %s, subtype: %s\n%s)' % (mbody, mtype, msubtype and msubtype.name, debug_info))

            # check message values
            if message_values:
                self.assertMessageFields(message, message_values)

            # check notifications and prepare assert data
            email_groups = {}
            status_groups = {
                'exception': {'email_lst': [], 'partners': []},
                'outgoing': {'email_lst': [], 'partners': []},
            }
            self.assertEqual(len(message.notification_ids), len(message_info['notif']))
            for recipient in message_info['notif']:
                # sanity check
                extra_keys = set(recipient.keys()) - {
                    'check_send',
                    'email_to',
                    'email_to_recipients',
                    'is_read',
                    'failure_reason',
                    'failure_type',
                    'group',
                    'partner',
                    'status',
                    'type',
                }
                if extra_keys:
                    raise ValueError(f'Unsupported recipient values: {extra_keys}')

                partner = recipient.get('partner', self.env['res.partner'])
                email_to_lst, email_cc_lst = recipient.get('email_to', []), recipient.get('email_cc', [])
                ntype, ngroup, nstatus = recipient['type'], recipient.get('group'), recipient.get('status', 'sent')
                nis_read = recipient.get('is_read', recipient['type'] != 'inbox')
                ncheck_send = recipient.get('check_send', True)

                if not ngroup:
                    ngroup = 'user'
                    if (partner and not partner.user_ids) or (not partner and email_to_lst):
                        ngroup = 'customer'
                    elif partner and partner.partner_share:
                        ngroup = 'portal'
                if ngroup not in email_groups:
                    email_groups[ngroup] = {
                        'email_cc_lst': [],
                        'email_to_lst': [],
                        'email_to_recipients': [],
                        'partners': self.env['res.partner'].sudo(),
                    }

                # find notification
                notif = notifications.filtered(
                    lambda n: n.mail_message_id == message
                    and ((partner and n.res_partner_id == partner) or n.mail_email_address in email_to_lst)
                    and n.notification_type == ntype
                )
                self.assertEqual(len(notif), 1,
                                 f'Mail: not found notification for {partner or email_to_lst} (type: {ntype}, message: {message.id})\n{debug_info}')
                self.assertEqual(notif.author_id, notif.mail_message_id.author_id)
                self.assertEqual(notif.is_read, nis_read)
                if 'failure_reason' in recipient:
                    self.assertEqual(notif.failure_reason, recipient['failure_reason'])
                if 'failure_type' in recipient:
                    self.assertEqual(notif.failure_type, recipient['failure_type'])
                self.assertEqual(notif.notification_status, nstatus)

                # prepare further asserts
                if ntype == 'email':
                    if nstatus in ('sent', 'ready', 'exception') and ncheck_send:
                        email_groups[ngroup]['partners'] += partner
                        if 'email_to_recipients' in recipient:
                            email_groups[ngroup]['email_to_recipients'] += recipient['email_to_recipients']
                        if email_cc_lst:
                            email_groups[ngroup]['email_cc_lst'] += email_cc_lst
                        if email_to_lst:
                            email_groups[ngroup]['email_to_lst'] += email_to_lst
                    # when force_send is False notably, notifications are ready and emails outgoing
                    if nstatus in ('ready', 'exception'):
                        state = 'outgoing' if nstatus == 'ready' else 'exception'
                        if partner:
                            status_groups[state]['partners'].append(partner)
                        if email_cc_lst:
                            status_groups[state]['email_lst'] += email_cc_lst
                        if email_to_lst:
                            status_groups[state]['email_lst'] += email_to_lst
                    # canceled: currently nothing checked - sent: already managed
                    elif nstatus in ('sent', 'canceled'):
                        pass
                    else:
                        raise NotImplementedError()

                done_notifs |= notif
            done_msgs |= message

            # check bus notifications that should be sent (hint: message author, multiple notifications)
            bus_notifications = message.notification_ids._filtered_for_web_client().filtered(lambda n: n.notification_status == 'exception')
            if bus_notifications:
                self.assertMessageBusNotifications(message, bus_notif_count)

            # check emails that should be sent (hint: mail.mail per group, email par recipient)
            email_values = {
                'body_content': mbody,
                'email_from': message.email_from,
                'references_content': [message.message_id],
            }
            if message_info.get('email_values'):
                email_values.update(message_info['email_values'])
            for group in email_groups.values():
                partners = group['partners']
                email_cc_lst = group['email_cc_lst']
                email_to_lst = group['email_to_lst']

                # compute expected mail status
                mail_status = 'sent'
                if partners and all(p in status_groups['exception']['partners'] for p in partners):
                    mail_status = 'exception'
                if email_to_lst and all(p in status_groups['exception']['email_lst'] for p in email_to_lst):
                    mail_status = 'exception'
                if partners and all(p in status_groups['outgoing']['partners'] for p in partners):
                    mail_status = 'outgoing'
                if email_to_lst and all(p in status_groups['outgoing']['email_lst'] for p in email_to_lst):
                    mail_status = 'outgoing'
                if not self.mail_unlink_sent and (partners or email_to_lst):
                    self.assertMailMail(
                        partners,
                        mail_status,
                        author=message_info.get('mail_mail_values', {}).get('author_id', message.author_id),
                        content=mbody,
                        email_to_all=email_to_lst,
                        email_to_recipients=group['email_to_recipients'] or None,
                        email_values=email_values,
                        fields_values=message_info.get('mail_mail_values'),
                        mail_message=message,
                    )
                else:
                    for partner in partners:
                        self.assertSentEmail(
                            message.author_id if message.author_id else message.email_from,
                            partner,
                            **email_values
                        )
                    if email_to_lst:
                        self.assertSentEmail(
                            message.author_id if message.author_id else message.email_from,
                            email_to_lst,
                            **email_values,
                        )

            if not any(p for recipients in email_groups.values() for p in recipients):
                self.assertNoMail(self.env['res.partner'], email_to=email_addrs, mail_message=message, author=message.author_id)

        return done_msgs, done_notifs