def _find_sent_email(self, email_from, emails_to, subject=None, body=None, attachment_names=None):
        """ Find an outgoing email based on from / to and optional subject, body
        and attachment names when having conflicts.

        :return sent_email: an outgoing email generated during the mock;
        """
        sent_emails = [
            mail for mail in self._mails
            if set(mail['email_to']) == set(emails_to) and mail['email_from'] == email_from
        ]
        if len(sent_emails) > 1:
            # try to better filter
            sent_email = next((mail for mail in sent_emails
                               if (subject is None or mail['subject'] == subject)
                               and (body is None or mail['body'] == body)
                               and (attachment_names is None
                                    or set(attachment_names) == set(attachment[0] for attachment in mail['attachments']))
                               ), False)
        else:
            sent_email = sent_emails[0] if sent_emails else False

        if not sent_email:
            debug_info = '\n'.join(
                f"From: {mail['email_from']} - To {mail['email_to']}"
                for mail in self._mails
            )
            raise AssertionError(
                f'sent mail not found for email_to {emails_to} from {email_from}'
                f'(optional: subject {subject})'
                f'\n--MOCK DATA\n{debug_info}'
            )

        return sent_email