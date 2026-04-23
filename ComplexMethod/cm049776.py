def _find_mail_mail_wemail(self, email_to, status, mail_message=None, author=None, content=None, email_from=None):
        """ Find a mail.mail record based on various parameters, notably a list
        of email to (string emails).

        :param email_to: either matching mail.email_to value, either a mail sent
          to a single recipient whose email is email_to;

        :return mail: a ``mail.mail`` record generated during the mock and matching
          given parameters and filters;
        """
        filtered = self._filter_mail(status=status, mail_message=mail_message, author=author, content=content, email_from=email_from)
        for mail in filtered:
            if (mail.email_to == email_to and not mail.recipient_ids) or (not mail.email_to and mail.recipient_ids.email == email_to):
                break
        else:
            debug_info = '\n'.join(
                f'From: {mail.author_id} ({mail.email_from}) - To: {mail.email_to} / {sorted(mail.recipient_ids.mapped("email"))} (State: {mail.state})'
                for mail in self._new_mails
            )
            raise AssertionError(
                f'mail.mail not found for message {mail_message} / status {status} / email_to {email_to} / '
                f'author {author} ({email_from})\n-- MOCK DATA\n{debug_info}'
            )
        return mail