def _gateway_mail_reply(self, template, mail=None, email=None,
                            force_email_from=False, force_email_to=False,
                            force_return_path=False, cc=False,
                            extra=False, use_references=True, extra_references=False, use_in_reply_to=False,
                            target_model='mail.test.gateway', target_field='name',
                            debug_log=False):
        """ Low-level helper tool to simulate a reply through mailgateway.

        :param mail.mail mail: mail.mail to which we are replying
        :param email.Message email: email to which we are replying
        """
        if not mail and not email:
            raise ValueError('Wrong usage of _gateway_mail_reply')
        message_id = (mail and mail.message_id) or email['message_id']
        original_reply_to = (mail and mail.reply_to) or (email and email['reply_to'])
        original_to = (mail and mail.email_to) or (email and email['email_to'][0])
        original_subject = (mail and mail.subject) or (email and email['subject'])

        extra = f'{extra}\n' if extra else ''
        # compute reply headers
        if use_in_reply_to:
            extra = f'{extra}In-Reply-To:\r\n\t{message_id}\n'
        if use_references:
            extra = f'{extra}References:\r\n\t{message_id}\n'
            if extra_references:
                extra = f'{extra}\r{extra_references}\n'

        return self.format_and_process(
            template,
            force_email_from or original_to,
            force_email_to or original_reply_to,
            cc=cc,
            extra=extra,
            return_path=force_return_path or original_to,
            subject=f'Re: {original_subject}',
            target_field=target_field,
            target_model=target_model,
            debug_log=debug_log,
        )