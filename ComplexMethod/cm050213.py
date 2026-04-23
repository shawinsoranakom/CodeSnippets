def test_mail_mail_send_exceptions_recipients_partners(self):
        """ Test various use case with exceptions and errors and see how they are
        managed and stored at mail and notification level. """
        mail, notification = self.test_mail, self.test_notification

        mail.write({'email_from': 'test.user@test.example.com', 'email_to': False})
        partners_falsy = self.env['res.partner'].create([
            {'name': 'Name %s' % email, 'email': email}
            for email in self.emails_falsy
        ])
        partners_invalid = self.env['res.partner'].create([
            {'name': 'Name %s' % email, 'email': email}
            for email in self.emails_invalid
        ])
        partners_invalid_ascii = self.env['res.partner'].create([
            {'name': 'Name %s' % email, 'email': email}
            for email in self.emails_invalid_ascii
        ])
        partners_valid = self.env['res.partner'].create([
            {'name': 'Name %s' % email, 'email': email}
            for email in self.emails_valid
        ])

        # void values
        for partner in partners_falsy:
            with self.subTest(partner_email=partner.email):
                self._reset_data()
                mail.write({'recipient_ids': [(5, 0), (4, partner.id)]})
                notification.write({'res_partner_id': partner.id})
                with self.mock_mail_gateway():
                    mail.send(raise_exception=False)
                self.assertEqual(mail.failure_reason, self.env['ir.mail_server'].NO_VALID_RECIPIENT)
                self.assertEqual(mail.failure_type, 'mail_email_invalid', 'Mail: void recipient partner: should be missing, not invalid')
                self.assertEqual(mail.state, 'exception')
                self.assertEqual(notification.failure_reason, self.env['ir.mail_server'].NO_VALID_RECIPIENT)
                self.assertEqual(notification.failure_type, 'mail_email_invalid', 'Mail: void recipient partner: should be missing, not invalid')
                self.assertEqual(notification.notification_status, 'exception')

        # wrong values
        for partner in partners_invalid:
            with self.subTest(partner_email=partner.email):
                self._reset_data()
                mail.write({'recipient_ids': [(5, 0), (4, partner.id)]})
                notification.write({'res_partner_id': partner.id})
                with self.mock_mail_gateway():
                    mail.send(raise_exception=False)
                self.assertEqual(mail.failure_reason, self.env['ir.mail_server'].NO_VALID_RECIPIENT)
                self.assertEqual(mail.failure_type, 'mail_email_invalid')
                self.assertEqual(mail.state, 'exception')
                self.assertEqual(notification.failure_reason, self.env['ir.mail_server'].NO_VALID_RECIPIENT)
                self.assertEqual(notification.failure_type, 'mail_email_invalid')
                self.assertEqual(notification.notification_status, 'exception')

        # ascii ko
        for partner in partners_invalid_ascii:
            with self.subTest(partner_email=partner.email):
                self._reset_data()
                mail.write({'recipient_ids': [(5, 0), (4, partner.id)]})
                notification.write({'res_partner_id': partner.id})
                with self.mock_mail_gateway():
                    mail.send(raise_exception=False)
                self.assertEqual(mail.failure_reason, self.env['ir.mail_server'].NO_VALID_RECIPIENT)
                self.assertEqual(mail.failure_type, 'mail_email_invalid')
                self.assertEqual(mail.state, 'exception')
                self.assertEqual(notification.failure_reason, self.env['ir.mail_server'].NO_VALID_RECIPIENT)
                self.assertEqual(notification.failure_type, 'mail_email_invalid')
                self.assertEqual(notification.notification_status, 'exception')

        # ascii ok or just ok
        for partner in partners_valid:
            with self.subTest(partner_email=partner.email):
                self._reset_data()
                mail.write({'recipient_ids': [(5, 0), (4, partner.id)]})
                notification.write({'res_partner_id': partner.id})
                with self.mock_mail_gateway():
                    mail.send(raise_exception=False)
                self.assertFalse(mail.failure_reason)
                self.assertFalse(mail.failure_type)
                self.assertEqual(mail.state, 'sent')
                self.assertFalse(notification.failure_reason)
                self.assertFalse(notification.failure_type)
                self.assertEqual(notification.notification_status, 'sent')