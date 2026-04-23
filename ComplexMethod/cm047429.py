def _prepare_email_message__(self, message, smtp_session):  # noqa: PLW3201
        """Prepare the SMTP information (from, to, message) before sending.

        :param message: the email.message.Message to send, information like the
            Return-Path, the From, etc... will be used to find the smtp_from and to smtp_to
        :param smtp_session: the opened SMTP session to use to authenticate the sender

        :return: smtp_from, smtp_to_list, message
            smtp_from: email to used during the authentication to the mail server
            smtp_to_list: list of email address which will receive the email
            message: the email.message.Message to send
        """
        # Use the default bounce address **only if** no Return-Path was
        # provided by caller.  Caller may be using Variable Envelope Return
        # Path (VERP) to detect no-longer valid email addresses.
        # context may force a value, e.g. mail.alias.domain usage
        bounce_address = self.env.context.get('domain_bounce_address') or message['Return-Path'] or self._get_default_bounce_address() or message['From']

        smtp_from = message['From'] or bounce_address
        assert smtp_from, self.NO_FOUND_SMTP_FROM

        smtp_to_list = self._prepare_smtp_to_list(message, smtp_session)
        assert smtp_to_list, self.NO_VALID_RECIPIENT

        # Try to not spoof the mail from headers; fetch session-based or contextualized
        # values for encapsulation computation
        from_filter = getattr(smtp_session, 'from_filter', False)
        smtp_from = getattr(smtp_session, 'smtp_from', False) or smtp_from
        notifications_email = email_normalize(
            self.env.context.get('domain_notifications_email') or self._get_default_from_address()
        )
        if notifications_email and email_normalize(smtp_from) == notifications_email and email_normalize(message['From']) != notifications_email:
            smtp_from = encapsulate_email(message['From'], notifications_email)

        # alter message
        self._alter_message__(message, smtp_from, smtp_to_list)

        # Check if it's still possible to put the bounce address as smtp_from
        if self._match_from_filter(bounce_address, from_filter):
            # Mail headers FROM will be spoofed to be able to receive bounce notifications
            # Because the mail server support the domain of the bounce address
            smtp_from = bounce_address

        # The email's "Envelope From" (Return-Path) must only contain ASCII characters.
        smtp_from_rfc2822 = extract_rfc2822_addresses(smtp_from)
        if not smtp_from_rfc2822:
            raise AssertionError(
                self.NO_VALID_FROM,
                f"Malformed 'Return-Path' or 'From' address: {smtp_from} - "
                "It should contain one valid plain ASCII email"
            )
        smtp_from = smtp_from_rfc2822[-1]

        return smtp_from, smtp_to_list, message