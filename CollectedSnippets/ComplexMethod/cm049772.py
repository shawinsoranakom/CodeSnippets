def gateway_mail_reply_from_smtp_email(self, template, source_smtp_to_list,
                                           reply_all=False, add_to_lst=False, cc=False,
                                           force_email_from=False, force_return_path=False,
                                           extra=False, use_references=True, extra_references=False, use_in_reply_to=False,
                                           debug_log=False,
                                           target_model='mail.test.gateway'):
        """ Tool to simulate a reply, based on outgoing SMTP emails.

        :param list source_smtp_to_list: find outgoing SMTP email based on their
          SMTP To header (should be a singleton list actually);
        """
        # find SMTP email based on recipients
        smtp_email = next(
            (m for m in self.emails if m['smtp_to_list'] == source_smtp_to_list),
            False
        )
        if not smtp_email:
            raise AssertionError(f'Not found SMTP email for {source_smtp_to_list}')
        # find matching mail.mail
        email = next(
            (m for m in self._mails if sorted(email_normalize(addr) for addr in m['email_to']) == sorted(source_smtp_to_list)),
            False
        )
        if not email:
            raise AssertionError(f'Not found matching mail.mail for {source_smtp_to_list}')

        # compute reply "To": either "reply-to" of email, either all recipients + reply_to - replier itself
        if not reply_all:
            replying_to = email['reply_to']
        else:
            replying_to = ','.join([email['reply_to']] + [
                email for email in email_split_and_format_normalize(smtp_email['msg_to'])
                if email_normalize(email) not in source_smtp_to_list]
            )
        if add_to_lst:
            replying_to = f'{replying_to},{",".join(add_to_lst)}'
        with RecordCapturer(self.env['mail.message']) as capture_messages, \
             self.mock_mail_gateway():
            self._gateway_mail_reply(
                template, email=email,
                force_email_from=force_email_from, force_email_to=replying_to,
                force_return_path=force_return_path, cc=cc,
                extra=extra, use_references=use_references, extra_references=extra_references, use_in_reply_to=use_in_reply_to,
                debug_log=debug_log,
                target_model=target_model,
            )
        return capture_messages.records