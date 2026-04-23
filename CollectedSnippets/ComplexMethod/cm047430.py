def _prepare_smtp_to_list(self, message, smtp_session):
        """ Prepare SMTP To address list, based on To / Cc / Bcc.

        Optional 'send_validated_to' context key filter restricts addresses to
        be part of that list.

        Optional 'send_smtp_skip_to' context key holds a recipients block list
        """
        email_to = message['To']
        email_cc = message['Cc']
        email_bcc = message['Bcc']

        # Support optional pre-validated To list, used notably when formatted
        # emails may create fake emails using extract_rfc2822_addresses, e.g.
        # '"Bike@Home" <email@domain.com>' which can be considered as containing
        # 2 emails by extract_rfc2822_addresses
        validated_to = self.env.context.get('send_validated_to') or []

        # Support optional skip To list
        skip_to_lst = self.env.context.get('send_smtp_skip_to') or []

        # All recipient addresses must only contain ASCII characters
        return [
            address
            for base in [email_to, email_cc, email_bcc]
            # be sure a given address does not return duplicates (but duplicates
            # in final smtp to list is still ok)
            for address in tools.misc.unique(extract_rfc2822_addresses(base))
            if (
                address and (not validated_to or address in validated_to)
                and email_normalize(address, strict=False) not in skip_to_lst
            )
        ]