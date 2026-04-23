def _find_mail_mail_wpartners(self, recipients, status, mail_message=None, author=None, content=None, email_from=None):
        """ Find a mail.mail record based on various parameters, notably a list
        of recipients (partners).

        :param recipients: a ``res.partner`` recordset Check all of them are in mail
          recipients to find the right mail.mail record;

        :return mail: a ``mail.mail`` record generated during the mock and matching
          given parameters and filters;
        """
        filtered = self._filter_mail(status=status, mail_message=mail_message, author=author, content=content, email_from=email_from)
        for mail in filtered:
            if all(p in mail.recipient_ids for p in recipients):
                break
        else:
            debug_info = '\n'.join(
                f'From: {mail.author_id} ({mail.email_from}) - To: {sorted(mail.recipient_ids.ids)} (State: {mail.state})'
                for mail in self._new_mails
            )
            author_info = f'{author.name} ({author.id})' if isinstance(author, self.env['res.partner'].__class__) else author
            recipients_info = f'Missing: {[f"{r.name} ({r.id})" for r in recipients if r.id not in filtered.recipient_ids.ids]}'
            raise AssertionError(
                f'mail.mail not found for message {mail_message} / status {status} / recipients {sorted(recipients.ids)} / '
                f'author {author_info}, email_from ({email_from})\n{recipients_info}\n{debug_info}'
            )
        return mail