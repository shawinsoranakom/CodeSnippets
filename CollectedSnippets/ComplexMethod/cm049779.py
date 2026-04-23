def assertNotSentEmail(self, recipients=None, message_id=None):
        """Check no email was generated during gateway mock.

        :param recipients:
            List of partner for which we will check that no email have been sent
            Or list of email address
            If empty, we will check that no email at all have been sent
        :param message_id:
            message-id associated with the email. Allows to identify emails originating
            from the a specific message in odoo.
        """
        mails = self._mails
        if message_id:
            mails = [mail for mail in self._mails if mail['message_id'] == message_id]
        if recipients:
            all_emails = [
                email_to.email_formatted if isinstance(email_to, self.env['res.partner'].__class__)
                else email_to
                for email_to in recipients
            ]

            mails = [
                mail
                for mail in mails
                if any(email in all_emails for email in mail['email_to'])
            ]

        self.assertEqual(len(mails), 0)