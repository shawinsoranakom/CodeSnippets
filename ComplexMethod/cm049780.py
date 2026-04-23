def assertSentEmail(self, author, recipients, **values):
        """ Tool method to ease the check of sent emails (going through the
        outgoing mail gateway, not actual <mail.mail> records).

        :param author: email author, either a string (email), either a partner
          record;
        :param recipients: list of recipients, each being either a string (email),
          either a partner record;
        :param values: dictionary of additional values to check email content;
        """
        direct_check = ['body_alternative', 'email_from', 'message_id', 'references', 'reply_to', 'subject']
        content_check = ['body_alternative_content', 'body_content', 'references_content']
        email_list_check = ['email_bcc', 'email_cc', 'email_to']
        other_check = ['attachments', 'attachments_info', 'body', 'headers']

        expected = {}
        for fname in direct_check + content_check + email_list_check + other_check:
            if fname in values:
                expected[fname] = values[fname]
        unknown = set(values.keys()) - set(direct_check + content_check + email_list_check + other_check)
        if unknown:
            raise NotImplementedError('Unsupported %s' % ', '.join(unknown))

        if isinstance(author, self.env['res.partner'].__class__):
            expected['email_from'] = formataddr((author.name, email_normalize(author.email, strict=False) or author.email))
        else:
            expected['email_from'] = author

        if 'email_to' in values:
            email_to_list = values['email_to']
        else:
            email_to_list = []
            for email_to in recipients:
                if isinstance(email_to, self.env['res.partner'].__class__):
                    email_to_list.append(formataddr((email_to.name, email_normalize(email_to.email, strict=False) or email_to.email)))
                else:
                    email_to_list.append(email_to)
        expected['email_to'] = email_to_list

        # fetch mail
        attachments = [attachment['name']
                       for attachment in values.get('attachments_info', [])
                       if 'name' in attachment]
        sent_mail = self._find_sent_email(
            expected['email_from'],
            expected['email_to'],
            subject=values.get('subject'),
            body=values.get('body'),
            attachment_names=attachments or None
        )
        debug_info = ''
        if not sent_mail:
            debug_info = '\n-'.join('From: %s-To: %s' % (mail['email_from'], mail['email_to']) for mail in self._mails)
        self.assertTrue(
            bool(sent_mail),
            'Expected mail from %s to %s not found in %s\n' % (expected['email_from'], expected['email_to'], debug_info)
        )

        # assert values
        for val in direct_check:
            if val in expected:
                self.assertEqual(expected[val], sent_mail[val], 'Value for %s: expected %s, received %s' % (val, expected[val], sent_mail[val]))
        if 'attachments' in expected:
            self.assertEqual(
                sorted(expected['attachments']), sorted(sent_mail['attachments']),
                'Value for %s: expected %s, received %s' % ('attachments', expected['attachments'], sent_mail['attachments'])
            )
        if 'attachments_info' in expected:
            attachments = sent_mail['attachments']
            for attachment_info in expected['attachments_info']:
                attachment = next((attach for attach in attachments if attach[0] == attachment_info['name']), False)
                self.assertTrue(
                    bool(attachment),
                    f'Attachment {attachment_info["name"]} not found in attachments',
                )
                if attachment_info.get('raw'):
                    self.assertEqual(attachment[1], attachment_info['raw'])
                if attachment_info.get('type'):
                    self.assertEqual(attachment[2], attachment_info['type'])
            self.assertEqual(len(expected['attachments_info']), len(attachments))
        if 'body' in expected:
            self.assertHtmlEqual(expected['body'], sent_mail['body'], 'Value for %s: expected %s, received %s' % ('body', expected['body'], sent_mail['body']))

        # beware to avoid list ordering differences (but Falsy values -> compare directly)
        for val in email_list_check:
            if expected.get(val):
                self.assertEqual(sorted(expected[val]), sorted(sent_mail[val]),
                                 'Value for %s: expected %s, received %s' % (val, expected[val], sent_mail[val]))
            elif val in expected:
                self.assertEqual(expected[val], sent_mail[val],
                                 'Value for %s: expected %s, received %s' % (val, expected[val], sent_mail[val]))

        # (partial) content check
        for val in content_check:
            if val == 'references_content' and val in expected:
                if not expected['references_content']:
                    self.assertFalse(sent_mail['references'])
                else:
                    for reference in expected['references_content']:
                        self.assertIn(reference, sent_mail['references'])
            else:
                if val in expected:
                    self.assertIn(
                        expected[val], sent_mail[val[:-8]],
                        'Value for %s: %s does not contain %s' % (val, sent_mail[val[:-8]], expected[val])
                    )

        if 'headers' in expected:
            # specific use case for X-Msg-To-Add: it is a comma-separated list of
            # email addresses, order is not important
            if 'X-Msg-To-Add' in sent_mail['headers'] and 'X-Msg-To-Add' in expected['headers']:
                msg_to_add = sent_mail['headers']['X-Msg-To-Add']
                exp_msg_to_add = expected['headers']['X-Msg-To-Add']
                self.assertEqual(
                    sorted(email_split_and_format_normalize(msg_to_add)),
                    sorted(email_split_and_format_normalize(exp_msg_to_add))
                )
            for key, value in expected['headers'].items():
                if key == 'X-Msg-To-Add':
                    continue
                self.assertTrue(key in sent_mail['headers'], f'Missing key {key}')
                found = sent_mail['headers'][key]
                self.assertEqual(found, value,
                                 f'Header value for {key} invalid, found {found} instead of {value}')
        return sent_mail