def _detect_is_bounce(self, message, message_dict):
        """Return True if the given email is a bounce email.

        Bounce alias: if any To contains bounce_alias@domain
        Bounce message (not alias)
            See http://datatracker.ietf.org/doc/rfc3462/?include_text=1
            As all MTA does not respect this RFC (googlemail is one of them),
            we also need to verify if the message come from "mailer-daemon"
        """
        # detection based on email_to
        bounce_aliases = self.env['mail.alias.domain'].search([]).mapped('bounce_email')
        email_to_list = [
            email_normalize(e) or e
            for e in email_split(message_dict['to'])
        ]
        if bounce_aliases and any(email in bounce_aliases for email in email_to_list):
            return True

        email_from = message_dict['email_from']
        email_from_localpart = (email_split(email_from) or [''])[0].split('@', 1)[0].lower()

        # detection based on email_from
        if email_from_localpart == 'mailer-daemon':
            return True

        # detection based on content type
        content_type = message.get_content_type()
        if content_type == 'multipart/report' or 'report-type=delivery-status' in content_type:
            return True

        return False