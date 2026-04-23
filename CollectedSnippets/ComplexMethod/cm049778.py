def assertNoMail(self, recipients, email_to=None, mail_message=None, author=None):
        """ Check no mail.mail and email was generated during gateway mock. """
        try:
            if recipients:
                self._find_mail_mail_wpartners(recipients, None, mail_message=mail_message, author=author)
            elif email_to is not None:
                self._find_mail_mail_wemail(email_to, None, mail_message=mail_message, author=author)
        except AssertionError:
            pass
        else:
            raise AssertionError('mail.mail exists for message %s / recipients %s / emails %s but should not exist' % (mail_message, recipients.ids, email_to or '/'))
        finally:
            self.assertNotSentEmail(recipients=list(recipients) + email_split_and_format_normalize(email_to or ''), message_id=mail_message and mail_message.message_id)