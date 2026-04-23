def assertSMSNotification(self, recipients_info, content, messages=None, check_sms=True, sent_unlink=False,
                              mail_message_values=None):
        """ Check content of notifications and sms.

          :param recipients_info: list[{
            'partner': res.partner record (may be empty),
            'number': number used for notification (may be empty, computed based on partner),
            'state': ready / pending / sent / exception / canceled (pending by default),
            'failure_type': optional: sms_number_missing / sms_number_format / sms_credit / sms_server
            }, { ... }]
          :param content: SMS content
          :param mail_message_values: dictionary of expected mail message fields values
        """
        partners = self.env['res.partner'].concat(*list(p['partner'] for p in recipients_info if p.get('partner')))
        numbers = [p['number'] for p in recipients_info if p.get('number')]
        # special case of void notifications: check for False / False notifications
        if not partners and not numbers:
            numbers = [False]
        base_domain = [
            '|', ('res_partner_id', 'in', partners.ids),
            '&', ('res_partner_id', '=', False), ('sms_number', 'in', numbers),
            ('notification_type', '=', 'sms')
        ]
        if messages is not None:
            base_domain += [('mail_message_id', 'in', messages.ids)]
        notifications = self.env['mail.notification'].search(base_domain)

        self.assertEqual(notifications.mapped('res_partner_id'), partners)

        for recipient_info in recipients_info:
            # sanity check
            extra_keys = recipient_info.keys() - {
                # notification
                'failure_reason',
                'failure_type',
                'state',
                # sms
                'sms_fields_values',
                # recipient
                'number',
                'partner',
                'recipient_check_sms',
            }
            if extra_keys:
                raise ValueError(f'Unsupported values: {extra_keys}')

            partner = recipient_info.get('partner', self.env['res.partner'])
            number = recipient_info.get('number')
            state = recipient_info.get('state', 'pending')
            if number is None and partner:
                number = partner._phone_format()

            notif = notifications.filtered(lambda n: n.res_partner_id == partner and n.sms_number == number and n.notification_status == state)

            debug_info = ''
            if not notif:
                debug_info = '\n'.join(
                    f'To: {notif.sms_number} ({notif.res_partner_id}) - (State: {notif.notification_status})'
                    for notif in notifications
                )
            self.assertTrue(notif, 'SMS: not found notification for %s (number: %s, state: %s)\n%s' % (partner, number, state, debug_info))
            self.assertEqual(notif.author_id, notif.mail_message_id.author_id, 'SMS: Message and notification should have the same author')
            for field_name, expected_value in (mail_message_values or {}).items():
                self.assertEqual(notif.mail_message_id[field_name], expected_value)
            if 'failure_reason' in recipient_info:
                self.assertEqual(notif.failure_reason, recipient_info['failure_reason'])
            if state not in {'process', 'sent', 'ready', 'canceled', 'pending'}:
                self.assertEqual(notif.failure_type, recipient_info['failure_type'])

            if recipient_info.get('recipient_check_sms', check_sms):
                fields_values = recipient_info.get('sms_fields_values') or {}
                if state in {'process', 'pending', 'sent'}:
                    if sent_unlink:
                        self.assertSMSIapSent([number], content=content)
                    else:
                        self.assertSMS(partner, number, state, content=content, fields_values=fields_values)
                elif state == 'ready':
                    self.assertSMS(partner, number, 'outgoing', content=content, fields_values=fields_values)
                elif state == 'exception':
                    self.assertSMS(partner, number, 'error', failure_type=recipient_info['failure_type'], content=content, fields_values=fields_values)
                elif state == 'canceled':
                    self.assertSMS(partner, number, 'canceled', failure_type=recipient_info['failure_type'], content=content, fields_values=fields_values)
                else:
                    raise NotImplementedError('Not implemented')

        if messages is not None:
            sanitize_tags = {**tools.mail.SANITIZE_TAGS}
            sanitize_tags['remove_tags'] = [*sanitize_tags['remove_tags'] + ['a']]
            with patch('odoo.tools.mail.SANITIZE_TAGS', sanitize_tags):
                for message in messages:
                    self.assertEqual(content, tools.html2plaintext(tools.html_sanitize(message.body)).rstrip('\n'))