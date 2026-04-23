def _assertMailMail(self, mail, recipients_list, status,
                        email_to_all=None, email_to_recipients=None,
                        author=None, content=None,
                        fields_values=None, email_values=None):
        """ Assert mail.mail record values and maybe related emails. Allow
        asserting their content. Records to check are the one generated when
        using mock (mail.mail and outgoing emails).

        :param mail: a ``mail.mail`` record;
        :param recipients_list: an ``res.partner`` recordset or a list of
          emails (both are supported, see ``_find_mail_mail_wpartners`` and
          ``_find_mail_mail_wemail``);
        :param status: mail.mail state used to filter mails. If ``sent`` this method
          also check that emails have been sent trough gateway;
        :param email_to_recipients: used for assertSentEmail to find email based
          on 'email_to' when doing the match directly based on recipients_list
          being partners it nos easy (e.g. multi emails, ...);
        :param author: see ``_find_mail_mail_wpartners``;
        :param content: if given, check it is contained within mail html body;
        :param email_to_all: list of email addresses used in email_to, checking
        all of them are in the same email. This is in addition to checking recipients
        individually.;
        :param fields_values: if given, should be a dictionary of field names /
          values allowing to check ``mail.mail`` additional values (subject,
          reply_to, ...);
        :param email_values: if given, should be a dictionary of keys / values
          allowing to check sent email additional values (if any).
          See ``assertSentEmail``;
        """
        self.assertTrue(bool(mail))
        if content:
            self.assertIn(content, mail.body_html)

        # specific check for message_id being in references: we don't care about
        # actual value, just that they are set and message_id present in references
        references_message_id_check = (email_values or {}).pop('references_message_id_check', False)
        if references_message_id_check:
            message_id = mail['message_id']
            self.assertTrue(message_id, 'Mail: expected value set for message_id')
            self.assertIn(message_id, mail.references, 'Mail: expected message_id to be part of references')
            email_values = dict({'message_id': message_id, 'references': mail.references}, **(email_values or {}))

        for fname, expected_fvalue in (fields_values or {}).items():
            with self.subTest(fname=fname, expected_fvalue=expected_fvalue):
                if fname == 'headers':
                    fvalue = literal_eval(mail[fname])
                    # specific use case for X-Msg-To-Add: it is a comma-separated list of
                    # email addresses, order is not important
                    if 'X-Msg-To-Add' in fvalue and 'X-Msg-To-Add' in expected_fvalue:
                        msg_to_add = fvalue['X-Msg-To-Add']
                        exp_msg_to_add = expected_fvalue['X-Msg-To-Add']
                        self.assertEqual(
                            sorted(email_split_and_format_normalize(msg_to_add)),
                            sorted(email_split_and_format_normalize(exp_msg_to_add))
                        )
                        fvalue = dict(fvalue)
                        fvalue.pop('X-Msg-To-Add')
                        expected_fvalue = dict(expected_fvalue)
                        expected_fvalue.pop('X-Msg-To-Add')
                        self.assertDictEqual(fvalue, expected_fvalue)
                    else:
                        self.assertDictEqual(fvalue, expected_fvalue)
                elif fname == 'attachments_info':
                    for attachment_info in expected_fvalue:
                        attachment = next((attach for attach in mail.attachment_ids if attach.name == attachment_info['name']), False)
                        self.assertTrue(
                            bool(attachment),
                            f'Attachment {attachment_info["name"]} not found in attachments',
                        )
                        if attachment_info.get('raw'):
                            self.assertEqual(attachment[1], attachment_info['raw'])
                        if attachment_info.get('type'):
                            self.assertEqual(attachment[2], attachment_info['type'])
                    self.assertEqual(len(expected_fvalue), len(mail.attachment_ids))
                else:
                    self.assertEqual(
                        mail[fname], expected_fvalue,
                        'Mail: expected %s for %s, got %s' % (expected_fvalue, fname, mail[fname])
                    )
        if status == 'sent':
            if email_to_recipients:
                recipients = email_to_recipients  # already formatted
            else:
                recipients = [[r] for r in recipients_list]  # one partner -> list of a single email
            for recipient in recipients:
                with self.subTest(recipient=recipient):
                    self.assertSentEmail(
                        email_values['email_from'] if email_values and email_values.get('email_from') else author,
                        recipient,
                        **(email_values or {})
                    )
            if email_to_all:
                self.assertSentEmail(
                    email_values['email_from'] if email_values and email_values.get('email_from') else author,
                    email_to_all,
                    **(email_values or {}))