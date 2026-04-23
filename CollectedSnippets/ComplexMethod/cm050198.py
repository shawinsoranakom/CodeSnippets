def test_mail_composer_post_parameters(self):
        """ Test various fields and tweaks in comment mode used for message_post
        parameters and process.. """
        # default behavior
        composer = self.env['mail.compose.message'].with_context(
            self._get_web_context(self.test_record)
        ).create({
            'body': '<p>Test Body</p>',
        })
        _mail, message = composer._action_send_mail()
        self.assertEqual(message.body, '<p>Test Body</p>')
        self.assertTrue(message.email_add_signature)
        self.assertFalse(message.email_layout_xmlid)
        self.assertEqual(message.message_type, 'comment', 'Mail: default message type with composer is user comment')
        self.assertEqual(message.subtype_id, self.env.ref('mail.mt_comment', 'Mail: default subtype is comment'))

        # tweaks
        composer = self.env['mail.compose.message'].with_context(
            self._get_web_context(self.test_record)
        ).create({
            'body': '<p>Test Body 2</p>',
            'email_add_signature': False,
            'email_layout_xmlid': 'mail.mail_notification_light',
            'message_type': 'notification',
            'subtype_id': self.env.ref('mail.mt_note').id,
            'partner_ids': [(4, self.partner_1.id), (4, self.partner_2.id)],
        })
        _mail, message = composer._action_send_mail()
        self.assertEqual(message.body, '<p>Test Body 2</p>')
        self.assertFalse(message.email_add_signature)
        self.assertEqual(message.email_layout_xmlid, 'mail.mail_notification_light')
        self.assertEqual(message.message_type, 'notification')
        self.assertEqual(message.subtype_id, self.env.ref('mail.mt_note'))

        # subtype through xml id
        composer = self.env['mail.compose.message'].with_context(
            self._get_web_context(self.test_record),
            default_subtype_xmlid='mail.mt_note',
        ).create({
            'body': '<p>Default subtype through xml id</p>',
        })
        _mail, message = composer._action_send_mail()
        self.assertEqual(message.subtype_id, self.env.ref('mail.mt_note'))

        # Check that the message created from the mail composer gets the values
        # we passed to the composer context. When we provide a custom `body`
        # and `email_add_signature` flag, the message should keep those values
        # and should not add any signature to the message body.
        composer = self.env['mail.compose.message'].with_context(
            self._get_web_context(self.test_record),
            default_body='<p>Hello world</p>',
            default_email_add_signature=False
        ).create({})
        _mail, message = composer._action_send_mail()
        self.assertFalse(message.email_add_signature)
        self.assertEqual(message.body, '<p>Hello world</p>')

        composer = self.env['mail.compose.message'].with_context(
            self._get_web_context(self.test_record),
            default_body='<p>Hi there</p>',
            default_email_add_signature=True
        ).create({})
        _mail, message = composer._action_send_mail()
        self.assertTrue(message.email_add_signature)
        self.assertEqual(message.body, '<p>Hi there</p>')

        # check author notification parameters support
        self.assertTrue(self.user_employee.partner_id in self.test_record.message_partner_ids)
        for notify_author, notify_author_mention, add_pid, should_mention in [
            (False, False, False, False),  # never add, even in pids
            (False, False, True, False),  # never add, even in pids
            (False, True, False, False),  # needs to be in pids
            (False, True, True, True),  # needs to be in pids
            (True, False, False, True),
        ]:
            with self.subTest(notify_author=notify_author, notify_author_mention=notify_author_mention, add_pid=add_pid):
                composer = self.env['mail.compose.message'].with_user(self.env.user).with_context(
                    self._get_web_context(self.test_record),
                ).create({
                    'body': 'Test Own Notify',
                    'message_type': 'comment',
                    'notify_author': notify_author,
                    'notify_author_mention': notify_author_mention,
                    'partner_ids': [(4, self.env.user.partner_id.id)] if add_pid else [],
                    'subtype_id': self.env.ref('mail.mt_comment').id,
                })
                _mail, message = composer._action_send_mail()
                self.assertEqual(message.author_id, self.user_employee.partner_id)
                if should_mention:
                    self.assertTrue(self.user_employee.partner_id in message.notified_partner_ids)
                else:
                    self.assertFalse(self.user_employee.partner_id in message.notified_partner_ids)

        # check notification control parameter support
        self.assertEqual(self.test_record.message_partner_ids, self.partner_employee + self.partner_employee_2)
        for notify_skip_followers in (False, True):
            with self.subTest(notify_skip_followers=notify_skip_followers):
                composer = self.env['mail.compose.message'].with_user(self.env.user).with_context(
                    self._get_web_context(self.test_record),
                ).create({
                    'body': 'Test Notify Params',
                    'message_type': 'comment',
                    'notify_skip_followers': notify_skip_followers,
                    'partner_ids': [(4, self.partner_admin.id)],
                    'subtype_id': self.env.ref('mail.mt_comment').id,
                })
                _mail, message = composer._action_send_mail()
                if notify_skip_followers:
                    self.assertEqual(
                        message.notified_partner_ids, self.partner_admin,
                        'notify_skip_followers parameter is either broken, either not propagated')
                else:
                    self.assertEqual(message.notified_partner_ids, self.partner_employee_2 + self.partner_admin,
                                     'classic notify: followers + recipients - author')
                self.assertEqual(message.partner_ids, self.partner_admin)

        # check notification UI control parameters
        for option in (False, 'reply_all', 'forward'):
            with self.subTest(option=option):
                composer = self.env['mail.compose.message'].with_user(self.env.user).with_context(
                    self._get_web_context(self.test_record),
                ).create({
                    'body': 'Test Notify Params',
                    'message_type': 'comment',
                    'composition_comment_option': option,
                    'partner_ids': [(4, self.partner_admin.id)],
                    'subtype_id': self.env.ref('mail.mt_comment').id,
                })
                _mail, message = composer._action_send_mail()
                if option == 'forward':
                    self.assertEqual(
                        message.notified_partner_ids, self.partner_admin,
                        'Either forward is broken, either notify_skip_followers parameter is broken')
                else:
                    self.assertEqual(message.notified_partner_ids, self.partner_employee_2 + self.partner_admin,
                                        'classic notify: followers + recipients - author')
                self.assertEqual(message.partner_ids, self.partner_admin)