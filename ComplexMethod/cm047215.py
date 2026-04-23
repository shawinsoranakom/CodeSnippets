def assertSMTPEmailsSent(self, smtp_from=None, smtp_to_list=None,
                             message_from=None, msg_from=None,
                             mail_server=None, from_filter=None,
                             emails_count=1,
                             msg_cc_lst=None, msg_to_lst=None):
        """Check that the given email has been sent. If one of the parameter is
        None it is just ignored and not used to retrieve the email.

        :param smtp_from: FROM used for the authentication to the mail server
        :param smtp_to_list: List of destination email address
        :param message_from: FROM used in the SMTP headers
        :param mail_server: used to compare the 'from_filter' as an alternative
          to using the from_filter parameter
        :param from_filter: from_filter of the <ir.mail_server> used to send the
          email. False means 'match everything';'
        :param emails_count: the number of emails which should match the condition
        :param msg_cc_lst: optional check msg_cc value of email;
        :param msg_to_lst: optional check msg_to value of email;

        :return: True if at least one email has been found with those parameters
        """
        if from_filter is not None and mail_server:
            raise ValueError('Invalid usage: use either from_filter either mail_server')

        if from_filter is None and mail_server is not None:
            from_filter = mail_server.from_filter
        matching_emails = list(filter(
            lambda email:
                (smtp_from is None or smtp_from == email['smtp_from'])
                and (smtp_to_list is None or smtp_to_list == email['smtp_to_list'])
                and (message_from is None or 'From: %s' % message_from in email['message'])
                # might have header being name <email> instead of "name" <email>, to check
                and (msg_from is None or (msg_from == email['msg_from'] or msg_from == email['msg_from_fmt']))
                and (from_filter is None or from_filter == email['from_filter']),
            self.emails,
        ))

        debug_info = ''
        matching_emails_count = len(matching_emails)
        if matching_emails_count != emails_count:
            debug_info = '\n'.join(
                f"SMTP-From: {email['smtp_from']}, SMTP-To: {email['smtp_to_list']}, "
                f"Msg-From: {email['msg_from']}, Msg-To: {email['msg_to']}, From_filter: {email['from_filter']})"
                for email in self.emails
            )
        self.assertEqual(
            matching_emails_count, emails_count,
            msg=f'Incorrect emails sent: {matching_emails_count} found, {emails_count} expected'
                f'\nConditions\nSMTP-From: {smtp_from}, SMTP-To: {smtp_to_list}, Msg-From: {message_from or msg_from}, From_filter: {from_filter}'
                f'\nNot found in\n{debug_info}'
        )
        if msg_to_lst is not None:
            for email in matching_emails:
                self.assertListEqual(sorted(email_split_and_format(email['msg_to'])), sorted(msg_to_lst))
        if msg_cc_lst is not None:
            for email in matching_emails:
                self.assertListEqual(sorted(email_split_and_format(email['msg_cc'])), sorted(msg_cc_lst))