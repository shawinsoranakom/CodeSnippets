def _filter_mail(self, status=None, mail_message=None, author=None, content=None, email_from=None):
        """ Filter mail generated during mock, based on common parameters

        :param status: state of mail.mail. If not void use it to filter mail.mail
          record;
        :param mail_message: optional check/filter on mail_message_id field aka
          a ``mail.message`` record;
        :param author: optional check/filter on author_id field aka a ``res.partner``
          record;
        :param content: optional check/filter on content, aka body_html (using an
          assertIn, not a pure equality check);
        :param email_from: optional check/filter on email_from field (may differ from
          author, used notably in case of concurrent mailings to distinguish emails);
        """
        filtered = self._new_mails.env['mail.mail']
        for mail in self._new_mails:
            if status is not None and mail.state != status:
                continue
            if mail_message is not None and mail.mail_message_id != mail_message:
                continue
            if author is not None and mail.author_id != author:
                continue
            if content is not None and content not in mail.body_html:
                continue
            if email_from is not None and mail.email_from != email_from:
                continue
            filtered += mail
        return filtered