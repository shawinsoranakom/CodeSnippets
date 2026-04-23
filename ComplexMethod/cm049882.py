def _message_parse_extract_bounce(self, email_message, message_dict):
        """ Parse email and extract bounce information to be used in future
        processing.

        :param email_message: an email.message instance;
        :param message_dict: dictionary holding already-parsed values;

        :return: a dict with bounce-related values will be added, containing

          * is_bounce: whether the email is recognized as a bounce email;
          * bounced_email: email that bounced (normalized);
          * bounce_partner: res.partner recordset whose email_normalized =
            bounced_email;
          * bounced_msg_ids: list of message_ID references (<...@myserver>) linked
            to the email that bounced;
          * bounced_message: if found, mail.message recordset matching bounced_msg_ids;
        """
        if not isinstance(email_message, EmailMessage):
            raise TypeError('message must be an email.message.EmailMessage at this point')

        is_bounce = self._detect_is_bounce(email_message, message_dict)
        if not is_bounce:
            return {'is_bounce': False}

        email_part = next((part for part in email_message.walk() if part.get_content_type() in {'message/rfc822', 'text/rfc822-headers'}), None)
        if not email_part:
            # In the case of a bounce message (e.g. bounce message of GMX), the "rfc822"
            # email part might not be always present. In that case we fallback to "multipart/report".
            email_part = next(
                (part for part in email_message.walk() if part.get_content_type() == 'multipart/report'),
                None,
            )

        dsn_part = next((part for part in email_message.walk() if part.get_content_type() == 'message/delivery-status'), None)

        bounced_email = False
        bounced_partner = self.env['res.partner'].sudo()
        if dsn_part and len(dsn_part.get_payload()) > 1:
            dsn = dsn_part.get_payload()[1]
            final_recipient_data = decode_message_header(dsn, 'Final-Recipient')
            # old servers may hold void or invalid Final-Recipient header
            if final_recipient_data and ";" in final_recipient_data:
                bounced_email = email_normalize(final_recipient_data.split(';', 1)[1].strip())
            if bounced_email:
                bounced_partner = self.env['res.partner'].sudo().search([('email_normalized', '=', bounced_email)])

        bounced_msg_ids = False
        bounced_message = self.env['mail.message'].sudo()
        if email_part:
            if email_part.get_content_type() == 'text/rfc822-headers':
                # Convert the message body into a message itself
                email_payload = message_from_string(email_part.get_content(), policy=email.policy.SMTP)
            else:
                email_payload = email_part.get_payload()[0]
            bounced_message, bounced_msg_ids = self._get_bounced_message_data(email_payload, message_dict)

        if bounced_message and not bounced_partner and len(bounced_message.notification_ids.res_partner_id) == 1:
            # if the original recipient was not found,
            # try to find the recipient based on parent <mail.message> notification
            bounced_partner = bounced_message.notification_ids.res_partner_id[0]
            bounced_email = bounced_partner.email

        return {
            'bounced_email': bounced_email,
            'bounced_partner': bounced_partner,
            'bounced_msg_ids': bounced_msg_ids,
            'bounced_message': bounced_message,
            'is_bounce': True,
        }