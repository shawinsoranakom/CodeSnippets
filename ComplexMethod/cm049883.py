def message_parse(self, message, save_original=False):
        """ Parses an email.message.Message representing an RFC-2822 email
        and returns a generic dict holding the message details.

        Note that partner finding is delegated to a post processing as it is
        better done using gateway record as context e.g. to check for
        followers, ... see '_message_parse_post_process'.

        :param message: email to parse
        :type message: email.message.Message
        :param bool save_original: whether the returned dict should include
            an ``original`` attachment containing the source of the message
        :rtype: dict
        :return: A dict with the following structure, where each field may not
            be present if missing in original message::

                { 'message_id': msg_id,
                  'subject': subject,
                  'email_from': from,
                  'to': to + delivered-to,
                  'cc': cc,
                  'recipients': delivered-to + to + cc + resent-to + resent-cc,
                  'body': unified_body,
                  'references': references,
                  'in_reply_to': in-reply-to,
                  'is_bounce': True if it has been detected as a bounce email
                  'parent_id': parent mail.message based on in_reply_to or references,
                  'is_internal': answer to an internal message (note),
                  'date': date,
                  'attachments': [('file1', 'bytes'),
                                  ('file2', 'bytes')}
                }
        """
        if not isinstance(message, EmailMessage):
            raise ValueError(_('Message should be a valid EmailMessage instance'))
        msg_dict = {'message_type': 'email'}

        message_id = message.get('Message-Id')
        if not message_id:
            # Very unusual situation, be we should be fault-tolerant here
            message_id = "<%s@localhost>" % time.time()
            _logger.debug('Parsing Message without message-id, generating a random one: %s', message_id)
        msg_dict['message_id'] = message_id.strip()

        if message.get('Subject'):
            msg_dict['subject'] = decode_message_header(message, 'Subject')

        email_from = decode_message_header(message, 'From', separator=',')
        email_cc = decode_message_header(message, 'cc', separator=',')
        email_from_list = email_split_and_format(email_from)
        email_cc_list = email_split_and_format(email_cc)
        msg_dict['email_from'] = email_from_list[0] if email_from_list else email_from
        msg_dict['from'] = msg_dict['email_from']  # compatibility for message_new
        msg_dict['cc'] = ','.join(email_cc_list) if email_cc_list else email_cc
        # Delivered-To is a safe bet in most modern MTAs, but we have to fallback on To + Cc values
        # for all the odd MTAs out there, as there is no standard header for the envelope's `rcpt_to` value.
        msg_dict['recipients'] = ','.join(set(formatted_email
            for address in [
                decode_message_header(message, 'Delivered-To', separator=','),
                decode_message_header(message, 'To', separator=','),
                decode_message_header(message, 'Cc', separator=','),
                decode_message_header(message, 'Resent-To', separator=','),
                decode_message_header(message, 'Resent-Cc', separator=',')
            ] if address
            for formatted_email in email_split_and_format(address))
        )
        email_to_list = list({
            formatted_email
            for address in [
                decode_message_header(message, 'Delivered-To', separator=','),
                decode_message_header(message, 'To', separator=',')
            ] if address
            for formatted_email in email_split_and_format(address)
        })
        msg_dict['to'] = ','.join(email_to_list)
        # filtered to / cc, excluding aliases
        recipients_normalized_all = email_normalize_all(f'{msg_dict["to"]},{msg_dict["cc"]}')
        alias_emails = self.env['mail.alias.domain'].sudo()._find_aliases(recipients_normalized_all)
        msg_dict['cc_filtered'] = ','.join(
            cc for cc in email_cc_list if email_normalize(cc) not in alias_emails
        )
        msg_dict['to_filtered'] = ','.join(
            to for to in email_to_list if email_normalize(to) not in alias_emails
        )

        # compute references to find if email_message is a reply to an existing thread
        msg_dict['references'] = decode_message_header(message, 'References')
        msg_dict['in_reply_to'] = decode_message_header(message, 'In-Reply-To').strip()

        if message.get('Date'):
            try:
                date_hdr = decode_message_header(message, 'Date')
                parsed_date = dateutil.parser.parse(date_hdr, fuzzy=True)
                if parsed_date.utcoffset() is None:
                    # naive datetime, so we arbitrarily decide to make it
                    # UTC, there's no better choice. Should not happen,
                    # as RFC2822 requires timezone offset in Date headers.
                    stored_date = parsed_date.replace(tzinfo=pytz.utc)
                else:
                    stored_date = parsed_date.astimezone(tz=pytz.utc)
            except Exception:
                _logger.info('Failed to parse Date header %r in incoming mail '
                             'with message-id %r, assuming current date/time.',
                             message.get('Date'), message_id)
                stored_date = datetime.datetime.now()
            msg_dict['date'] = fields.Datetime.to_string(stored_date)

        msg_dict.update(self._message_parse_extract_from_parent(self._get_parent_message(msg_dict)))
        msg_dict.update(self._message_parse_extract_bounce(message, msg_dict))
        msg_dict.update(self._message_parse_extract_payload(message, msg_dict, save_original=save_original))
        return msg_dict