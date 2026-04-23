def test_personal_mail_server_limit(self):
        # Test the limit per personal mail servers
        TEST_LIMIT = 5
        self.env['ir.config_parameter'].set_param('mail.server.personal.limit.minutes', str(TEST_LIMIT))
        user_1, user_2 = self.user_1, self.user_2
        mail_server_1, mail_server_2 = self.mail_server_1, self.mail_server_2

        with self.mock_datetime_and_now("2025-01-01 20:02:23"):
            mails_user_1 = self.env["mail.mail"].with_user(user_1).sudo().create([
                {'state': 'outgoing', 'email_to': 'target@test.com', 'email_from': user_1.email}
                for i in range(22)
            ])
            mails_user_2 = self.env["mail.mail"].with_user(user_2).sudo().create([
                {'state': 'outgoing', 'email_to': 'target@test.com', 'email_from': user_2.email}
                for i in range(17)
            ])
            mails_other = self.env["mail.mail"].create([
                {'state': 'outgoing', 'email_to': 'target@test.com', 'email_from': user_1.email}
                for i in range(25)
            ])

        mails = mails_other + mails_user_1 + mails_user_2

        self.assertEqual(mail_server_1.owner_limit_count, 0)
        self.assertFalse(mail_server_1.owner_limit_time)

        DATE_SEND_1 = datetime(2025, 1, 1, 20, 5, 23)
        with (
            self.mock_smtplib_connection(),
            self.mock_datetime_and_now(DATE_SEND_1),
            self.assert_mail_sent_then_scheduled(mails_user_1, len(mails_user_1), 5, DATE_SEND_1),
            self.assert_mail_sent_then_scheduled(mails_user_2, len(mails_user_2), 5, DATE_SEND_1),
        ):
            mails.send()

        for personal_server in (mail_server_1, mail_server_2):
            self.assertEqual(personal_server.owner_limit_count, TEST_LIMIT)
            self.assertEqual(personal_server.owner_limit_time, DATE_SEND_1.replace(second=0))

        self.assertEqual(self.connect_mocked.call_count, 3, "Called once for each mail server")

        # Check that the email not related to personal mail server are all sent
        self.assertEqual(set(mails_other.mapped('state')), {'sent'})

        # User 1 continues sending emails
        # Because emails are still in the queue, we delay all of them
        with self.mock_datetime_and_now("2025-01-01 20:04:23"):
            new_mails_user_1 = self.env["mail.mail"].with_user(user_1).sudo().create([
                {'state': 'outgoing', 'email_to': 'target@test.com', 'email_from': user_1.email}
                for i in range(12)
            ])
        mails_user_1 |= new_mails_user_1

        DATE_SEND_2 = datetime(2025, 1, 1, 20, 5, 23)
        with (
            self.mock_smtplib_connection(),
            self.mock_datetime_and_now(DATE_SEND_2),
            self.assert_mail_sent_then_scheduled(new_mails_user_1, 12, 0, DATE_SEND_2),
        ):
            new_mails_user_1.send()

        self.assertEqual(mail_server_1.owner_limit_count, TEST_LIMIT)
        self.assertEqual(mail_server_1.owner_limit_time, DATE_SEND_2.replace(second=0))

        # One minute later, we can send again
        DATE_SEND_3 = datetime(2025, 1, 1, 20, 6, 23)
        processed = (mails_user_1 | new_mails_user_1).filtered(
            lambda m: not m.scheduled_date or m.scheduled_date <= DATE_SEND_3)
        with (
            self.mock_smtplib_connection(),
            self.mock_datetime_and_now(DATE_SEND_3),
            self.assert_mail_sent_then_scheduled(processed, 10, 5, DATE_SEND_3),
        ):
            self.env['mail.mail'].process_email_queue()

        self.assertEqual(mail_server_1.owner_limit_count, TEST_LIMIT)
        self.assertEqual(mail_server_1.owner_limit_time, DATE_SEND_3.replace(second=0))

        # The CRON run in one minute later, we can 5 more emails
        DATE_SEND_5 = datetime(2025, 1, 1, 20, 7, 23)
        with (
            self.mock_smtplib_connection(),
            self.mock_datetime_and_now(DATE_SEND_5),
            self.assert_mail_sent_then_scheduled(mails_user_1, 15, 5, DATE_SEND_5),
        ):
            self.env['mail.mail'].process_email_queue()

        self.assertEqual(mail_server_1.owner_limit_count, TEST_LIMIT)
        self.assertEqual(mail_server_1.owner_limit_time, DATE_SEND_5.replace(second=0))

        # The CRON is late compared to the scheduled mails,
        # it should re-schedule the mails, starting from the current time
        # Should send in priority the old mails
        DATE_SEND_6 = datetime(2025, 1, 1, 20, 25, 23)
        with (
            self.mock_smtplib_connection(),
            self.mock_datetime_and_now(DATE_SEND_6),
            self.assert_mail_sent_then_scheduled(mails_user_1, 19, 5, DATE_SEND_6),
        ):
            self.env['mail.mail'].process_email_queue()

        self.assertEqual(mail_server_1.owner_limit_count, TEST_LIMIT)
        self.assertEqual(mail_server_1.owner_limit_time, DATE_SEND_6.replace(second=0))

        # Finish sending the email
        for i in range(2):
            DATE_SEND_7 = datetime(2025, 1, 1, 20, 26 + i, 23)
            with self.mock_smtplib_connection(), self.mock_datetime_and_now(DATE_SEND_7):
                self.env['mail.mail'].process_email_queue()
            self.assertEqual(mail_server_1.owner_limit_count, TEST_LIMIT)
            self.assertEqual(mail_server_1.owner_limit_time, DATE_SEND_7.replace(second=0))

        DATE_SEND_8 = datetime(2025, 1, 1, 20, 28, 23)
        with self.mock_smtplib_connection(), self.mock_datetime_and_now(DATE_SEND_8):
            self.env['mail.mail'].process_email_queue()
        self.assertEqual(mail_server_1.owner_limit_count, 4)
        self.assertEqual(mail_server_1.owner_limit_time, DATE_SEND_8.replace(second=0))

        # We send 4 emails this minute, check that will send 1 and schedule the remaining
        new_mails_user_1 = self.env["mail.mail"].with_user(user_1).sudo().create([
            {'state': 'outgoing', 'email_to': 'target@test.com', 'email_from': user_1.email}
            for i in range(TEST_LIMIT)
        ])
        DATE_SEND_9 = datetime(2025, 1, 1, 20, 28, 23)
        with (
            self.mock_smtplib_connection(),
            self.mock_datetime_and_now(DATE_SEND_9),
            self.assert_mail_sent_then_scheduled(new_mails_user_1, len(new_mails_user_1), 1, DATE_SEND_9),
        ):
            self.env['mail.mail'].process_email_queue()
        self.assertEqual(mail_server_1.owner_limit_count, TEST_LIMIT)
        self.assertEqual(mail_server_1.owner_limit_time, DATE_SEND_9.replace(second=0))