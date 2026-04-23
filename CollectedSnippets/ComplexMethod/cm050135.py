def _routing_handle_bounce(self, email_message, message_dict):
        # In addition, an auto blacklist rule check if the email can be blacklisted
        # to avoid sending mails indefinitely to this email address.
        # This rule checks if the email bounced too much. If this is the case,
        # the email address is added to the blacklist in order to avoid continuing
        # to send mass_mail to that email address. If it bounced too much times
        # in the last month and the bounced are at least separated by one week,
        # to avoid blacklist someone because of a temporary mail server error,
        # then the email is considered as invalid and is blacklisted.
        super(MailThread, self)._routing_handle_bounce(email_message, message_dict)

        bounced_email = message_dict['bounced_email']
        bounced_msg_ids = message_dict['bounced_msg_ids']
        bounced_partner = message_dict['bounced_partner']

        if bounced_msg_ids:
            self.env['mailing.trace'].set_bounced(
                domain=[('message_id', 'in', bounced_msg_ids)],
                bounce_message=tools.html2plaintext(message_dict.get('body') or ''))
        if bounced_email:
            three_months_ago = fields.Datetime.to_string(datetime.datetime.now() - datetime.timedelta(weeks=13))
            stats = self.env['mailing.trace'].search(['&', '&', ('trace_status', '=', 'bounce'), ('write_date', '>', three_months_ago), ('email', '=ilike', bounced_email)]).mapped('write_date')
            if len(stats) >= BLACKLIST_MAX_BOUNCED_LIMIT and (not bounced_partner or any(p.message_bounce >= BLACKLIST_MAX_BOUNCED_LIMIT for p in bounced_partner)):
                if max(stats) > min(stats) + datetime.timedelta(weeks=1):
                    self.env['mail.blacklist'].sudo()._add(
                        bounced_email,
                        message=Markup('<p>%s</p>') % _('This email has been automatically added in blocklist because of too much bounced.')
                    )